import { Injectable } from '@nestjs/common';
import { buildEvaluationFromAnswerMap } from 'src/shared/exams/evaluation';
import { PrismaService } from 'src/infrastructure/prisma/prisma.service';
import { findExamDocumentByAnyId, findQuestionDocumentsByAnyIds } from 'src/shared/mongo/read-models';
import { HistoryService } from 'src/modules/history/history.service';
import { requireStudentByIdentity } from 'src/modules/students/student-identity';
import { SubmitExamDto } from './dto/submit-exam.dto';

@Injectable()
export class ExamsService {
	constructor(
		private readonly prisma: PrismaService,
		private readonly historyService: HistoryService,
	) { }

	async submit(dto: SubmitExamDto) {
		const student = await requireStudentByIdentity(this.prisma, dto.student_id);
		const userId = student.user_id;
		const exam = await findExamDocumentByAnyId(this.prisma, dto.exam_id);
		const submittedQuestionIds = dto.full_exam.sections.flatMap((section) =>
			section.questions.map((question) => question.question_id),
		);
		const questions = submittedQuestionIds.length === 0
			? []
			: await findQuestionDocumentsByAnyIds(this.prisma, submittedQuestionIds);
		const answerMap = new Map(
			questions.map((question) => [question.question_id, question]),
		);
		const submittedAnswerMap = new Map(
			dto.full_exam.sections.flatMap((section) =>
				section.questions.map((question) => [question.question_id, question.student_answer ?? ''] as const),
			),
		);
		const orderedQuestions = submittedQuestionIds.map((questionId) => ({
			question_id: questionId,
			type: answerMap.get(questionId)?.type ?? null,
			correct_answer: answerMap.get(questionId)?.correct_answer ?? '',
		}));
		const evaluation = buildEvaluationFromAnswerMap(orderedQuestions, submittedAnswerMap);
		const score = exam?.generated ? null : evaluation.score;
		const studentAnswerRecords = dto.student_ans?.length
			? dto.student_ans
			: dto.full_exam.sections.flatMap((section) =>
				section.questions.map((question) => ({
					question_id: question.question_id,
					student_answer: question.student_answer ?? '',
				})),
			);

		if (student.is_first_login) {
			await this.prisma.student.update({
				where: {
					mongo_id: student.mongo_id,
				},
				data: {
					is_first_login: false,
				},
			});
		}

		await this.historyService.create(
			userId,
			{
				intent: 'VIEW_ANALYSIS',
				exam_id: dto.exam_id,
				student_ans: studentAnswerRecords,
				correct_count: evaluation.correct_count,
				score: score ?? undefined,
			},
			{
				aiPayload: {
					intent: 'GRADE_SUBMISSION',
					user_id: userId,
					exam_id: dto.exam_id,
					time_taken_seconds: dto.time_taken_seconds,
					student_ans: studentAnswerRecords,
					correct_count: evaluation.correct_count,
					total_questions: evaluation.total_questions,
					score,
					per_question: evaluation.per_question,
					full_exam: dto.full_exam,
					metadata: {
						// Adaptive needs goal/context to plan the *next* backlog,
						// not only the just-finished submission. Keep these values
						// close to the grading payload so the AI service can shape
						// practice recommendations around the learner's target.
						learning_goal: student.learning_goal ?? null,
						student_grade: student.grade ?? null,
						school: student.school ?? null,
					},
				},
			},
		);

		return {
			...evaluation,
			score,
		};
	}
}
