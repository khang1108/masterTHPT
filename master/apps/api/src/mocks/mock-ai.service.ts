import { Injectable, NotFoundException } from '@nestjs/common';
import { MOCK_EXAMS_BY_DOCUMENT_ID } from './data/mock-exams';
import { ExamDetail } from './types';

type EvaluateSubmissionInput = {
	student_id: string;
	exam_id: string;
	time_taken_seconds: number;
	full_exam: {
		exam_id: string;
		sections: Array<{
			type: string;
			questions: Array<{
				id: string;
				student_answer: string;
			}>;
		}>;
	};
	sections?: Array<{
		type: string;
		questions: Array<{
			id: string;
			student_answer: string;
		}>;
	}>;
};

@Injectable()
export class MockAiService {
	private clone<T>(value: T): T {
		return JSON.parse(JSON.stringify(value)) as T;
	}

	getExamByDocumentId(documentId: string): ExamDetail {
		const exam = MOCK_EXAMS_BY_DOCUMENT_ID[documentId];
		if (!exam) {
			throw new NotFoundException('Khong tim thay noi dung de thi');
		}

		return this.clone(exam);
	}

	generateExam(input: { sourceType: string; subject?: string; examType?: string }) {
		const source = this.clone(MOCK_EXAMS_BY_DOCUMENT_ID['doc-001']);
		source.exam_id = `generated-${Date.now()}`;
		source.source_type = input.sourceType;
		source.subject = input.subject ?? source.subject;
		source.exam_type = input.examType ?? source.exam_type;
		source.total_questions = source.sections.reduce(
			(total, section) => total + section.questions.length,
			0,
		);

		return source;
	}

	evaluate(submission: EvaluateSubmissionInput) {
		const sourceExam =
			MOCK_EXAMS_BY_DOCUMENT_ID[submission.exam_id] ??
			MOCK_EXAMS_BY_DOCUMENT_ID['doc-001'];

		const exam = this.clone(sourceExam);
		const totalQuestions = exam.sections.reduce(
			(acc, section) => acc + section.questions.length,
			0,
		);
		const pointPerQuestion = totalQuestions > 0 ? 10 / totalQuestions : 0;

		const answerMap = new Map<
			string,
			{
				correct_answer: string;
			}
		>();

		exam.sections.forEach((section) => {
			section.questions.forEach((question) => {
				answerMap.set(question.id, {
					correct_answer: question.correct_answer,
				});
			});
		});

		const per_question: Array<{
			question_id: string;
			student_answer: string;
			correct_answer: string;
			is_correct: boolean;
			score: number;
			max_score: number;
			reasoning: string;
			error_analysis: null | {
				error_type: string;
				remedial: string;
			};
		}> = [];

		let totalScore = 0;

		const submittedSections =
			submission.full_exam?.sections?.length > 0
				? submission.full_exam.sections
				: (submission.sections ?? []);

		submittedSections.forEach((section) => {
			section.questions.forEach((question) => {
				const expected = answerMap.get(question.id);
				if (!expected) {
					return;
				}

				const studentAnswer = (question.student_answer ?? '').trim();
				const correctAnswer = expected.correct_answer.trim();
				const isCorrect =
					studentAnswer.toUpperCase() === correctAnswer.toUpperCase();
				const score = isCorrect ? pointPerQuestion : 0;

				totalScore += score;

				per_question.push({
					question_id: question.id,
					student_answer: studentAnswer,
					correct_answer: correctAnswer,
					is_correct: isCorrect,
					score: Number(score.toFixed(2)),
					max_score: Number(pointPerQuestion.toFixed(2)),
					reasoning: isCorrect
						? 'Bạn trả lời đúng. Lập luận và cách tính phù hợp với đáp án chuẩn.'
						: `Bạn chưa đúng. Đáp án đúng là ${correctAnswer}. ãy xem lại lý thuyết và làm thêm bài tập tương tự.`,
					error_analysis: isCorrect
						? null
						: {
							error_type: 'KIEN_THUC_NEN (CONCEPT_ERROR)',
							remedial:
								'Ôn lại phần lý thuyết liên quan và làm 5 bài tập cùng dạng để củng cố.',
						},
				});
			});
		});

		const roundedScore = Number(totalScore.toFixed(2));

		return {
			total_score: roundedScore,
			max_score: 10.0,
			overall_analysis: {
				strengths:
					roundedScore >= 7
						? ['Nên tăng kiến thức khá', 'Khả năng xử lý câu hỏi cơ bản']
						: ['Đã nắm được một phần câu hỏi dễ', 'Có kiến thức nền tảng ban đầu'],
				weaknesses:
					roundedScore >= 7
						? ['Cần tối ưu tốc độ và độ chính xác ở câu khó']
						: ['Còn nhầm lẫn ở câu hỏi vận dụng', 'Cần củng cố kiến thức nền'],
				general_advice:
					roundedScore >= 7
						? 'Bạn đang ở mức tốt. Hãy luyện thêm để nâng điểm ở nhóm câu vận dụng cao.'
						: 'Cần tập trung ôn lại lý thuyết cơ bản và luyện đề theo từng chủ đề.',
			},
			per_question,
		};
	}
}
