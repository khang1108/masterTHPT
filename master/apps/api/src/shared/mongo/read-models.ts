import { Prisma } from '@prisma/client';
import { PrismaService } from 'src/infrastructure/prisma/prisma.service';

type RawMongoDocument = Record<string, unknown>;

type RawFindCommandResult = {
	cursor?: {
		firstBatch?: unknown[];
	};
};

type FindCommandOptions = {
	limit?: number;
	sort?: Record<string, 1 | -1>;
};

export type ExamReadModel = {
	mongo_id: string;
	id: string;
	subject: string;
	grade: number | null;
	exam_type: string;
	year: number | null;
	source: string | null;
	generated: boolean | null;
	questions: string[];
	total_questions: number | null;
	duration: number | null;
	created_at: string | null;
};

export type QuestionReadModel = {
	mongo_id: string;
	question_id: string;
	exam_id: string | null;
	question_index: number;
	type: string;
	content: string;
	content_latex: string | null;
	options: string[];
	correct_answer: string | null;
	has_image: boolean;
	image_url: string | null;
	discrimination_a: number | null;
	difficulty_b: number | null;
	topic_tags: string[];
	max_score: number | null;
};

export type HistoryReadModel = {
	mongo_id: string;
	intent: string;
	user_id: string;
	exam_id: string;
	student_ans: Prisma.JsonValue;
	correct_count: number | null;
	score: number | null;
	created_at: string | null;
};

const EXAM_PROJECTION = {
	_id: 1,
	id: 1,
	subject: 1,
	grade: 1,
	exam_type: 1,
	year: 1,
	source: 1,
	generated: 1,
	questions: 1,
	total_questions: 1,
	duration: 1,
	created_at: 1,
} as const;

const QUESTION_PROJECTION = {
	_id: 1,
	id: 1,
	question_id: 1,
	exam_id: 1,
	question_index: 1,
	type: 1,
	content: 1,
	content_latex: 1,
	options: 1,
	correct_answer: 1,
	has_image: 1,
	image_url: 1,
	discrimination_a: 1,
	difficulty_b: 1,
	topic_tags: 1,
	max_score: 1,
} as const;

const HISTORY_PROJECTION = {
	_id: 1,
	intent: 1,
	user_id: 1,
	exam_id: 1,
	student_ans: 1,
	correct_count: 1,
	score: 1,
	created_at: 1,
} as const;

function isPlainObject(value: unknown): value is RawMongoDocument {
	return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function toNumberOrNull(value: unknown) {
	if (typeof value === 'number' && Number.isFinite(value)) {
		return value;
	}

	if (typeof value === 'string' && value.trim().length > 0) {
		const parsed = Number(value);
		return Number.isFinite(parsed) ? parsed : null;
	}

	return null;
}

function toStringOrNull(value: unknown) {
	return typeof value === 'string' && value.trim().length > 0 ? value : null;
}

function toBooleanOrNull(value: unknown) {
	if (typeof value === 'boolean') {
		return value;
	}

	if (typeof value === 'string') {
		const normalized = value.trim().toLowerCase();
		if (normalized === 'true') {
			return true;
		}

		if (normalized === 'false') {
			return false;
		}
	}

	return null;
}

function toStringArray(value: unknown) {
	if (!Array.isArray(value)) {
		return [];
	}

	return value.filter((item): item is string => typeof item === 'string' && item.trim().length > 0);
}

function toMongoId(value: unknown) {
	if (typeof value === 'string' && value.trim().length > 0) {
		return value;
	}

	if (isPlainObject(value) && typeof value.$oid === 'string' && value.$oid.trim().length > 0) {
		return value.$oid;
	}

	return null;
}

function toIsoDateString(value: unknown) {
	if (typeof value === 'string' && value.trim().length > 0) {
		return value;
	}

	if (value instanceof Date && !Number.isNaN(value.getTime())) {
		return value.toISOString();
	}

	if (isPlainObject(value) && '$date' in value) {
		const rawDate = value.$date;
		if (typeof rawDate === 'string' && rawDate.trim().length > 0) {
			return rawDate;
		}

		if (typeof rawDate === 'number') {
			return new Date(rawDate).toISOString();
		}
	}

	return null;
}

function sanitizeJsonValue(value: unknown): Prisma.JsonValue {
	if (
		value === null ||
		typeof value === 'string' ||
		typeof value === 'number' ||
		typeof value === 'boolean'
	) {
		return value as Prisma.JsonValue;
	}

	if (Array.isArray(value)) {
		return value.map((item) => sanitizeJsonValue(item)) as Prisma.JsonArray;
	}

	if (isPlainObject(value)) {
		if (Object.keys(value).length === 1 && '$oid' in value) {
			return toMongoId(value) ?? null;
		}

		if (Object.keys(value).length === 1 && '$date' in value) {
			return toIsoDateString(value) ?? null;
		}

		const entries = Object.entries(value).map(([key, item]) => [key, sanitizeJsonValue(item)] as const);
		return Object.fromEntries(entries) as Prisma.JsonObject;
	}

	return String(value);
}

function extractDocuments(result: unknown) {
	if (!isPlainObject(result)) {
		return [];
	}

	const maybeResult = result as RawFindCommandResult;
	if (!maybeResult.cursor || !Array.isArray(maybeResult.cursor.firstBatch)) {
		return [];
	}

	return maybeResult.cursor.firstBatch.filter(isPlainObject);
}

function buildAnyIdFilter(ids: string[], primaryField = 'id', legacyFields: string[] = []) {
	const uniqueIds = [...new Set(ids.map((item) => item.trim()).filter((item) => item.length > 0))];
	if (uniqueIds.length === 0) {
		return null;
	}

	const objectIds = uniqueIds
		.filter((item) => /^[a-f0-9]{24}$/i.test(item))
		.map((item) => ({ $oid: item }));

	if (uniqueIds.length === 1) {
		const fieldFilters = [primaryField, ...legacyFields].map((field) => ({ [field]: uniqueIds[0] }));
		if (objectIds.length === 1) {
			return {
				$or: [
					...fieldFilters,
					{ _id: objectIds[0] },
				],
			};
		}

		return fieldFilters.length === 1 ? fieldFilters[0] : { $or: fieldFilters };
	}

	const fieldFilters = [primaryField, ...legacyFields].map((field) => ({ [field]: { $in: uniqueIds } }));
	if (objectIds.length > 0) {
		return {
			$or: [
				...fieldFilters,
				{ _id: { $in: objectIds } },
			],
		};
	}

	return fieldFilters.length === 1 ? fieldFilters[0] : { $or: fieldFilters };
}

async function runFindCommand(
	prisma: PrismaService,
	collection: string,
	filter: Record<string, unknown>,
	projection: Record<string, 1>,
	options: FindCommandOptions = {},
) {
	const command: Record<string, unknown> = {
		find: collection,
		filter,
		projection,
	};

	if (typeof options.limit === 'number') {
		command.limit = options.limit;
	}

	if (options.sort) {
		command.sort = options.sort;
	}

	const result = await prisma.$runCommandRaw(command as Prisma.InputJsonObject);
	return extractDocuments(result);
}

function normalizeExamDocument(document: RawMongoDocument): ExamReadModel | null {
	const mongoId = toMongoId(document._id);
	const id = toStringOrNull(document.id) ?? mongoId;

	if (!mongoId || !id) {
		return null;
	}

	return {
		mongo_id: mongoId,
		id,
		subject: toStringOrNull(document.subject) ?? '',
		grade: toNumberOrNull(document.grade),
		exam_type: toStringOrNull(document.exam_type) ?? '',
		year: toNumberOrNull(document.year),
		source: toStringOrNull(document.source),
		generated: toBooleanOrNull(document.generated),
		questions: toStringArray(document.questions),
		total_questions: toNumberOrNull(document.total_questions),
		duration: toNumberOrNull(document.duration),
		created_at: toIsoDateString(document.created_at),
	};
}

function normalizeQuestionDocument(document: RawMongoDocument): QuestionReadModel | null {
	const mongoId = toMongoId(document._id);
	const question_id =
		toStringOrNull(document.question_id) ??
		toStringOrNull(document.id) ??
		mongoId;

	if (!mongoId || !question_id) {
		return null;
	}

	const type = toStringOrNull(document.type) ?? '';
	const options = toStringArray(document.options);

	return {
		mongo_id: mongoId,
		question_id,
		exam_id: toStringOrNull(document.exam_id),
		question_index: toNumberOrNull(document.question_index) ?? 0,
		type,
		content: toStringOrNull(document.content) ?? '',
		content_latex: toStringOrNull(document.content_latex),
		options,
		correct_answer: toStringOrNull(document.correct_answer),
		has_image: toBooleanOrNull(document.has_image) ?? false,
		image_url: toStringOrNull(document.image_url),
		discrimination_a: toNumberOrNull(document.discrimination_a),
		difficulty_b: toNumberOrNull(document.difficulty_b),
		topic_tags: toStringArray(document.topic_tags),
		max_score: toNumberOrNull(document.max_score),
	};
}

function normalizeHistoryDocument(document: RawMongoDocument): HistoryReadModel | null {
	const mongoId = toMongoId(document._id);

	if (!mongoId) {
		return null;
	}

	return {
		mongo_id: mongoId,
		intent: toStringOrNull(document.intent) ?? '',
		user_id: toStringOrNull(document.user_id) ?? '',
		exam_id: toStringOrNull(document.exam_id) ?? '',
		student_ans: sanitizeJsonValue(document.student_ans),
		correct_count: toNumberOrNull(document.correct_count),
		score: toNumberOrNull(document.score),
		created_at: toIsoDateString(document.created_at),
	};
}

export async function findPublishedExamDocuments(prisma: PrismaService) {
	const documents = await runFindCommand(
		prisma,
		'exams',
		{ generated: false },
		EXAM_PROJECTION,
	);

	return documents
		.map(normalizeExamDocument)
		.filter((document): document is ExamReadModel => document !== null);
}

export async function findExamDocumentByAnyId(prisma: PrismaService, id: string) {
	const filter = buildAnyIdFilter([id]);
	if (!filter) {
		return null;
	}

	const documents = await runFindCommand(
		prisma,
		'exams',
		filter,
		EXAM_PROJECTION,
		{ limit: 1 },
	);

	return documents
		.map(normalizeExamDocument)
		.find((document): document is ExamReadModel => document !== null) ?? null;
}

export async function findExamDocumentsByAnyIds(prisma: PrismaService, ids: string[]) {
	const filter = buildAnyIdFilter(ids);
	if (!filter) {
		return [];
	}

	const documents = await runFindCommand(
		prisma,
		'exams',
		filter,
		EXAM_PROJECTION,
	);

	return documents
		.map(normalizeExamDocument)
		.filter((document): document is ExamReadModel => document !== null);
}

export async function findQuestionDocumentsByAnyIds(prisma: PrismaService, ids: string[]) {
	const filter = buildAnyIdFilter(ids, 'question_id', ['id']);
	if (!filter) {
		return [];
	}

	const documents = await runFindCommand(
		prisma,
		'questions',
		filter,
		QUESTION_PROJECTION,
	);

	return documents
		.map(normalizeQuestionDocument)
		.filter((document): document is QuestionReadModel => document !== null);
}

export async function findQuestionDocumentByAnyId(prisma: PrismaService, id: string) {
	const filter = buildAnyIdFilter([id], 'question_id', ['id']);
	if (!filter) {
		return null;
	}

	const documents = await runFindCommand(
		prisma,
		'questions',
		filter,
		QUESTION_PROJECTION,
		{ limit: 1 },
	);

	return documents
		.map(normalizeQuestionDocument)
		.find((document): document is QuestionReadModel => document !== null) ?? null;
}

export async function findHistoryDocumentsByUserId(prisma: PrismaService, userId: string) {
	const documents = await runFindCommand(
		prisma,
		'histories',
		{ user_id: userId },
		HISTORY_PROJECTION,
		{ sort: { created_at: -1 } },
	);

	return documents
		.map(normalizeHistoryDocument)
		.filter((document): document is HistoryReadModel => document !== null);
}

export async function findHistoryDocumentByUserAndId(prisma: PrismaService, userId: string, historyId: string) {
	if (!/^[a-f0-9]{24}$/i.test(historyId)) {
		return null;
	}

	const filter = {
		user_id: userId,
		_id: { $oid: historyId },
	};

	const documents = await runFindCommand(
		prisma,
		'histories',
		filter,
		HISTORY_PROJECTION,
		{ limit: 1 },
	);

	return documents
		.map(normalizeHistoryDocument)
		.find((document): document is HistoryReadModel => document !== null) ?? null;
}
