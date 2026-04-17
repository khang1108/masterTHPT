import { Injectable } from '@nestjs/common';
import { buildEvaluationFromAnswerMap } from 'src/shared/exams/evaluation';
import { PrismaService } from 'src/infrastructure/prisma/prisma.service';
import { findExamDocumentByAnyId, findQuestionDocumentsByAnyIds } from 'src/shared/mongo/read-models';
import { SubmitExamDto } from './dto/submit-exam.dto';

@Injectable()
export class ExamsService {
	constructor(
		private readonly prisma: PrismaService,
	) { }

	async submit(dto: SubmitExamDto) {
		const exam = await findExamDocumentByAnyId(this.prisma, dto.exam_id);
		const submittedQuestionIds = dto.full_exam.sections.flatMap((section) =>
			section.questions.map((question) => question.id),
		);
		const questions = submittedQuestionIds.length === 0
			? []
			: await findQuestionDocumentsByAnyIds(this.prisma, submittedQuestionIds);
		const answerMap = new Map(
			questions.map((question) => [question.id, question]),
		);
		const submittedAnswerMap = new Map(
			dto.full_exam.sections.flatMap((section) =>
				section.questions.map((question) => [question.id, question.student_answer ?? ''] as const),
			),
		);
		const orderedQuestions = submittedQuestionIds.map((questionId) => ({
			id: questionId,
			type: answerMap.get(questionId)?.type ?? null,
			correct_answer: answerMap.get(questionId)?.correct_answer ?? '',
		}));
		const evaluation = buildEvaluationFromAnswerMap(orderedQuestions, submittedAnswerMap);

		await this.prisma.student.updateMany({
			where: {
				id: dto.student_id,
				is_first_login: true,
			},
			data: {
				is_first_login: false,
			},
		});

		return {
			...evaluation,
			score: exam?.generated ? null : evaluation.score,
		};
	}
}
