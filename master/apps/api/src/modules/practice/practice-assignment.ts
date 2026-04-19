import { randomUUID } from 'crypto';
import { Prisma } from '@prisma/client';
import { Logger } from '@nestjs/common';
import { PrismaService } from 'src/infrastructure/prisma/prisma.service';

type AdaptiveSelectedQuestion = {
	question_id?: string;
	type?: string;
	content?: string;
	content_latex?: string | null;
	options?: string[];
	statements?: string[];
	correct_answer?: string | null;
	has_image?: boolean;
	image_url?: string | null;
	discrimination_a?: number | null;
	difficulty_b?: number | null;
	topic_tags?: string[];
	max_score?: number | null;
};

type AdaptiveResponseShape = {
	selected_questions?: AdaptiveSelectedQuestion[];
	profile_updates?: Record<string, unknown>;
	learner_profile?: Record<string, unknown>;
	feedback?: string | null;
};

type PersistAdaptivePracticeOptions = {
	userId: string;
	studentGrade?: number | null;
	requestText?: string;
	adaptiveResponse: AdaptiveResponseShape | null;
};

const logger = new Logger('PracticeAssignment');

function cleanString(value: unknown, fallback = '') {
	return typeof value === 'string' && value.trim().length > 0 ? value.trim() : fallback;
}

function cleanStringArray(value: unknown) {
	if (!Array.isArray(value)) {
		return [];
	}

	return value
		.filter((item): item is string => typeof item === 'string')
		.map((item) => item.trim())
		.filter((item) => item.length > 0);
}

function cleanNumber(value: unknown, fallback: number) {
	return typeof value === 'number' && Number.isFinite(value) ? value : fallback;
}

function normalizeSelectedQuestion(raw: AdaptiveSelectedQuestion, index: number) {
	const fallbackQuestionId = `adaptive-question-${randomUUID()}`;
	const rawQuestionId = cleanString(raw.question_id, '');
	const shouldMintFreshQuestionId =
		!rawQuestionId || rawQuestionId.startsWith('generated-') || rawQuestionId.startsWith('adaptive-question-');
	const questionId = shouldMintFreshQuestionId ? fallbackQuestionId : rawQuestionId;

	return {
		question_id: questionId,
		question_index: index + 1,
		type: cleanString(raw.type, 'multiple_choice'),
		content: cleanString(raw.content, 'Câu hỏi luyện tập chưa có nội dung.'),
		content_latex: typeof raw.content_latex === 'string' ? raw.content_latex : null,
		options: cleanStringArray(raw.options),
		statements: cleanStringArray(raw.statements),
		correct_answer:
			typeof raw.correct_answer === 'string' && raw.correct_answer.trim().length > 0
				? raw.correct_answer.trim()
				: null,
		has_image: Boolean(raw.has_image),
		image_url: typeof raw.image_url === 'string' && raw.image_url.trim().length > 0 ? raw.image_url.trim() : null,
		discrimination_a: cleanNumber(raw.discrimination_a, 1),
		difficulty_b: cleanNumber(raw.difficulty_b, 0),
		topic_tags: cleanStringArray(raw.topic_tags),
		max_score: typeof raw.max_score === 'number' && Number.isFinite(raw.max_score) ? raw.max_score : 1,
	};
}

async function ensureQuestionDocument(
	prisma: PrismaService,
	question: ReturnType<typeof normalizeSelectedQuestion>,
) {
	const existingQuestion = await prisma.question.findUnique({
		where: {
			question_id: question.question_id,
		},
		select: {
			question_id: true,
		},
	});

	if (existingQuestion) {
		return existingQuestion.question_id;
	}

	const createdQuestion = await prisma.question.create({
		data: {
			question_id: question.question_id,
			question_index: question.question_index,
			type: question.type,
			content: question.content,
			content_latex: question.content_latex ?? undefined,
			options: question.options,
			correct_answer: question.correct_answer ?? undefined,
			has_image: question.has_image,
			image_url: question.image_url ?? undefined,
			discrimination_a: question.discrimination_a,
			difficulty_b: question.difficulty_b,
			topic_tags: question.topic_tags,
			max_score: question.max_score ?? undefined,
		},
		select: {
			question_id: true,
		},
	});

	return createdQuestion.question_id;
}

export async function persistAdaptivePracticeSet(
	prisma: PrismaService,
	options: PersistAdaptivePracticeOptions,
) {
	const existingPractice = await prisma.practice.findUnique({
		where: {
			user_id: options.userId,
		},
		select: {
			exam_ids: true,
		},
	});
	const existingExamIds = existingPractice?.exam_ids ?? [];
	const selectedQuestions = Array.isArray(options.adaptiveResponse?.selected_questions)
		? options.adaptiveResponse?.selected_questions ?? []
		: [];

	if (selectedQuestions.length === 0) {
		logger.warn(`Adaptive response for user ${options.userId} does not contain selected_questions`);
		await prisma.practice.upsert({
			where: {
				user_id: options.userId,
			},
			update: {
				// Keep the current backlog intact when adaptive only updated the
				// learner profile but did not emit new practice items.
				exam_ids: existingExamIds,
			},
			create: {
				user_id: options.userId,
				exam_ids: existingExamIds,
			},
		});

		return {
			exam_ids: existingExamIds,
		};
	}

	const adaptiveTrace =
		options.adaptiveResponse?.profile_updates &&
		typeof options.adaptiveResponse.profile_updates === 'object' &&
		options.adaptiveResponse.profile_updates !== null
			? (options.adaptiveResponse.profile_updates as Record<string, unknown>).adaptive_trace
			: null;

	const createdExamIds: string[] = [];
	for (const [index, rawQuestion] of selectedQuestions.entries()) {
		const normalizedQuestion = normalizeSelectedQuestion(rawQuestion, index);
		const questionId = await ensureQuestionDocument(prisma, normalizedQuestion);
		const createdExam = await prisma.exam.create({
			data: {
				subject: 'Toán',
				grade: options.studentGrade ?? 12,
				exam_type: 'Luyện tập Adaptive',
				year: new Date().getFullYear(),
				source: 'ADAPTIVE_AGENT',
				generated: true,
				questions: [questionId],
				total_questions: 1,
				duration: 15,
				metadata: {
					source_type: 'adaptive_practice_question',
					practice_mode: 'leetcode',
					request_text: options.requestText ?? null,
					selection_index: index + 1,
					topic_tags: normalizedQuestion.topic_tags,
					adaptive_trace: adaptiveTrace,
				} as Prisma.InputJsonValue,
				created_at: new Date().toISOString(),
			},
			select: {
				id: true,
			},
		});
		createdExamIds.push(createdExam.id);
	}

	await prisma.practice.upsert({
		where: {
			user_id: options.userId,
		},
		update: {
			// Practice works like a rolling backlog of one-question exams. New
			// adaptive items are appended instead of replacing older unfinished
			// ones so the UI can render a LeetCode-style queue.
			exam_ids: [...new Set([...existingExamIds, ...createdExamIds])],
		},
		create: {
			user_id: options.userId,
			exam_ids: createdExamIds,
		},
	});

	logger.log(
		`Persisted ${createdExamIds.length} adaptive practice item(s) for user ${options.userId}`,
	);

	return {
		exam_ids: [...new Set([...existingExamIds, ...createdExamIds])],
	};
}
