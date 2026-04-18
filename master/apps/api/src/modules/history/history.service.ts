import { Prisma } from '@prisma/client';
import { Injectable, Logger, NotFoundException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { postToAiService } from 'src/shared/ai/ai-client';
import {
	ASCII_SECTION_NAME_BY_TYPE,
	buildExamSections,
	sortItemsByReferenceOrder,
} from 'src/shared/exams/exam-content';
import {
	buildEvaluationFromAnswerMap,
	normalizeHistoryStudentAnswers,
} from 'src/shared/exams/evaluation';
import { PrismaService } from 'src/infrastructure/prisma/prisma.service';
import { requireStudentByIdentity } from 'src/modules/students/student-identity';
import {
	findExamDocumentByAnyId,
	findExamDocumentsByAnyIds,
	findHistoryDocumentByUserAndId,
	findHistoryDocumentsByUserId,
	findQuestionDocumentsByAnyIds,
} from 'src/shared/mongo/read-models';
import { CreateHistoryDto } from './dto/create-history.dto';

type HistoryCreateOptions = {
	notifyAi?: boolean;
	aiPayload?: unknown;
};

@Injectable()
export class HistoryService {
	private readonly logger = new Logger(HistoryService.name);

	constructor(
		private readonly prisma: PrismaService,
		private readonly configService: ConfigService,
	) { }

	async create(userId: string, dto: CreateHistoryDto, options: HistoryCreateOptions = {}) {
		const student = await requireStudentByIdentity(this.prisma, userId);
		const canonicalUserId = student.user_id;
		// History is the source of truth for "what the student had answered"
		// at the moment they exited a completed flow.
		const history = await this.prisma.history.create({
			data: {
				intent: dto.intent,
				user_id: canonicalUserId,
				exam_id: dto.exam_id,
				student_ans: dto.student_ans as unknown as Prisma.InputJsonValue,
				correct_count: dto.correct_count,
				score: dto.score,
			},
			select: {
				mongo_id: true,
				intent: true,
				user_id: true,
				exam_id: true,
				student_ans: true,
				correct_count: true,
				score: true,
				created_at: true,
			},
		});

		if (dto.intent === 'EXAM_PRACTICE') {
			await this.removeCompletedPracticeExam(canonicalUserId, dto.exam_id);
		}

		const shouldNotifyAi = options.notifyAi ?? true;
		if (shouldNotifyAi && this.configService.get<string>('AI_API_BASE_URL')?.trim()) {
			const aiPayload = options.aiPayload ?? {
				// Practice completion still uses the lightweight analysis event so
				// existing AI consumers do not need to change for this flow.
				intent: 'VIEW_ANALYSIS',
				user_id: canonicalUserId,
				exam_id: dto.exam_id,
			};

			try {
				await postToAiService(this.configService, aiPayload);
			} catch (error) {
				this.logger.warn(`Failed to notify AI service for history ${history.mongo_id}: ${error instanceof Error ? error.message : 'Unknown error'}`);
			}
		}

		return history;
	}

	private async removeCompletedPracticeExam(userId: string, examId: string) {
		// Practice completion removes the exam from the student's assignment list
		// so the practice page can refresh into the next recommended set.
		const practice = await this.prisma.practice.findUnique({
			where: {
				user_id: userId,
			},
			select: {
				exam_ids: true,
			},
		});

		if (!practice || !practice.exam_ids.includes(examId)) {
			return;
		}

		const remainingExamIds = practice.exam_ids.filter((currentExamId) => currentExamId !== examId);

		await this.prisma.practice.update({
			where: {
				user_id: userId,
			},
			data: {
				exam_ids: remainingExamIds,
			},
		});
	}

	async list(userId: string) {
		const student = await requireStudentByIdentity(this.prisma, userId);
		// List view is intentionally light-weight: fetch histories first, then join only the
		// exam metadata needed to render cards in reverse chronological order.
		const histories = await findHistoryDocumentsByUserId(this.prisma, student.user_id);

		const examIds = [...new Set(histories.map((item) => item.exam_id))];
		const exams = await findExamDocumentsByAnyIds(this.prisma, examIds);
		const examMap = new Map<string, (typeof exams)[number]>();

		exams.forEach((exam) => {
			examMap.set(exam.id, exam);
			examMap.set(exam.mongo_id, exam);
		});

		return histories.map((history) => {
			const exam = examMap.get(history.exam_id);

			return {
				history_id: history.mongo_id,
				intent: history.intent,
				exam_id: history.exam_id,
				correct_count: history.correct_count ?? 0,
				score: history.score,
				created_at: history.created_at ?? '',
				subject: exam?.subject ?? 'Đề chưa xác định',
				grade: exam?.grade ?? null,
				exam_type: exam?.exam_type ?? '',
				source: exam?.source ?? 'Nguồn chưa cập nhật',
				total_questions: exam?.total_questions ?? 0,
				duration: exam?.duration ?? 0,
				year: exam?.year ?? null,
			};
		});
	}

	async getDetail(userId: string, historyId: string) {
		const student = await requireStudentByIdentity(this.prisma, userId);
		// Detail view rebuilds the original exam structure plus evaluation,
		// so the UI can behave like a read-only version of the exam room.
		const history = await findHistoryDocumentByUserAndId(this.prisma, student.user_id, historyId);

		if (!history) {
			throw new NotFoundException('Không tìm thấy lịch sử làm bài');
		}

		const exam = await findExamDocumentByAnyId(this.prisma, history.exam_id);

		if (!exam) {
			throw new NotFoundException('Không tìm thấy đề thi');
		}

		const questionIds = exam.questions ?? [];
		const questions = await findQuestionDocumentsByAnyIds(this.prisma, questionIds);
		const sortedQuestions = sortItemsByReferenceOrder(questionIds, questions);

		const answerMap = new Map(
			normalizeHistoryStudentAnswers(history.student_ans).map((item) => [item.question_id, item.student_answer]),
		);
		const sections = buildExamSections(sortedQuestions, ASCII_SECTION_NAME_BY_TYPE);
		const evaluation = buildEvaluationFromAnswerMap(sortedQuestions, answerMap);
		const correctCount = history.correct_count ?? evaluation.correct_count;
		const totalQuestions = sortedQuestions.length > 0 ? sortedQuestions.length : (exam.total_questions ?? 0);

		return {
			history_id: history.mongo_id,
			intent: history.intent,
			created_at: history.created_at ?? '',
			exam_id: exam.id,
			correct_count: correctCount,
			score: history.score ?? null,
			subject: exam.subject || 'Đề chưa xác định',
			grade: exam.grade ?? 0,
			exam_type: exam.exam_type || 'Đề chưa xác định',
			source: exam.source ?? 'Nguồn chưa cập nhật',
			total_questions: totalQuestions,
			duration_minutes: exam.duration ?? 0,
			sections,
			evaluation: {
				correct_count: correctCount,
				total_questions: totalQuestions,
				score: exam.generated ? null : evaluation.score,
				per_question: evaluation.per_question,
			},
		};
	}
}
