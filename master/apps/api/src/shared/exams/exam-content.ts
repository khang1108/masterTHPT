export type ExamMetadataShape = {
	source_type?: string;
	duration_minutes?: number;
};

export type SectionType = 'multiple_choice' | 'true_false' | 'short_ans';

export type SectionNameMap = Record<SectionType, string>;

export const ACCENTED_SECTION_NAME_BY_TYPE: SectionNameMap = {
	multiple_choice: 'Phần I: Trắc nghiệm nhiều lựa chọn',
	true_false: 'Phần II: Đúng sai',
	short_ans: 'Phần III: Trả lời ngắn',
};

export const ASCII_SECTION_NAME_BY_TYPE: SectionNameMap = {
	multiple_choice: 'Phan I: Trac nghiem nhieu lua chon',
	true_false: 'Phan II: Dung sai',
	short_ans: 'Phan III: Tra loi ngan',
};

type QuestionWithOrder = {
	id: string;
	question_index?: number;
};

type RenderableQuestion = QuestionWithOrder & {
	type: string;
	content: string;
	content_latex?: string | null;
	options: string[];
	statements: string[];
	has_image: boolean;
	image_url?: string | null;
};

export function sortItemsByReferenceOrder<T extends QuestionWithOrder>(
	referenceIds: string[],
	items: T[],
) {
	// Mongo/Prisma "in" queries do not guarantee the same order as the source id list.
	// We restore the exam-defined order here so every screen renders questions consistently.
	const itemOrder = new Map(referenceIds.map((itemId, index) => [itemId, index]));

	return [...items].sort((a, b) => {
		const aOrder = itemOrder.get(a.id);
		const bOrder = itemOrder.get(b.id);

		if (aOrder !== undefined && bOrder !== undefined) {
			return aOrder - bOrder;
		}

		if (aOrder !== undefined) {
			return -1;
		}

		if (bOrder !== undefined) {
			return 1;
		}

		return (a.question_index ?? 0) - (b.question_index ?? 0);
	});
}

export function buildExamSections(
	questions: RenderableQuestion[],
	sectionNameByType: SectionNameMap,
) {
	// Build response sections from a flat DB result so documents, onboarding,
	// and history review can share the same shaping logic.
	const sectionBuckets = new Map<SectionType, Array<{
		id: string;
		question_index: number;
		type: SectionType;
		content: string;
		options?: string[];
		statements?: string[];
		has_image: boolean;
		image_url?: string;
	}>>();

	for (const question of questions) {
		if (
			question.type !== 'multiple_choice' &&
			question.type !== 'true_false' &&
			question.type !== 'short_ans'
		) {
			// Ignore unknown question types until the frontend has a renderer for them.
			continue;
		}

		const normalizedType = question.type as SectionType;
		const current = sectionBuckets.get(normalizedType) ?? [];
		const options = Array.isArray(question.options) ? question.options : [];
		const statements = Array.isArray(question.statements) ? question.statements : [];

		current.push({
			id: question.id,
			question_index: question.question_index ?? 0,
			type: normalizedType,
			content: question.content_latex ?? question.content,
			options: options.length > 0 ? options : undefined,
			statements: statements.length > 0 ? statements : undefined,
			has_image: question.has_image,
			image_url: question.image_url ?? undefined,
		});
		sectionBuckets.set(normalizedType, current);
	}

	return (Object.keys(sectionNameByType) as SectionType[])
		.map((type) => ({
			type,
			section_name: sectionNameByType[type],
			questions: sectionBuckets.get(type) ?? [],
		}))
		.filter((section) => section.questions.length > 0);
}
