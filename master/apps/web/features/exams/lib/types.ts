import { ExamQuestion, ExamSection } from '@/shared/api/client';

export type QuestionSectionType = 'multiple_choice' | 'true_false' | 'short_answer';

export type FlatQuestion = {
	id: string;
	index: number;
	sectionType: QuestionSectionType;
	question: ExamQuestion;
};

export function flattenExamSections(sections: ExamSection[]): FlatQuestion[] {
	// Flatten sections once so every screen can navigate questions with the same shape.
	return sections.flatMap((section) =>
		section.questions.map((question) => ({
			id: question.id,
			index: question.question_index,
			sectionType: section.type,
			question,
		})),
	);
}
