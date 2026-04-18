import { MathText } from '@/features/exams/components/math-text';
import { getAlphabetLabel, parseOption, tokenToLabel } from '@/features/exams/lib/helpers';
import { FlatQuestion } from '@/features/exams/lib/types';
import { ExamEvaluationItem } from '@/shared/api/client';

type ResultAnswerPanelProps = {
	question: FlatQuestion;
	evaluation: ExamEvaluationItem;
};

// This read-only renderer mirrors EditableAnswerPanel, but focuses on explaining
// what happened after grading instead of collecting input.
export function ResultAnswerPanel({ question, evaluation }: ResultAnswerPanelProps) {
	if (question.sectionType === 'multiple_choice') {
		const selected = evaluation.student_answer.trim();
		const correctLabel = parseOption(evaluation.correct_answer).label;

		return (
			<div className="exam-mc-grid exam-result-panel">
				{question.question.options?.map((option) => {
					const parsed = parseOption(option);
					const isCorrectOption = parsed.label === correctLabel;
					const isStudentSelected = selected === parsed.label;
					const isWrongSelected = isStudentSelected && !isCorrectOption;

					return (
						<div
							key={`${question.question_id}-${parsed.label}`}
							className={`exam-mc-option exam-result-option ${isCorrectOption ? 'is-correct' : ''} ${isWrongSelected ? 'is-wrong' : ''}`}
						>
							<div className="exam-mc-option-main">
								<span className="exam-mc-badge">{parsed.label}</span>
								<MathText text={parsed.text} />
							</div>
							<span className={`exam-result-tag ${isCorrectOption ? 'is-correct' : isStudentSelected ? 'is-wrong' : ''}`}>
								{isCorrectOption ? 'Đúng' : isStudentSelected ? 'Bạn chọn' : ''}
							</span>
						</div>
					);
				})}
			</div>
		);
	}

	if (question.sectionType === 'true_false') {
		// True/false answers are still stored as comma-separated tokens,
		// so result rendering decodes them the same way as the input panel.
		const statements = question.question.statements ?? [];
		const studentTokens = evaluation.student_answer.split(',').map((item) => item.trim());
		const correctTokens = evaluation.correct_answer.split(',').map((item) => item.trim());

		return (
			<div className="exam-tf-table exam-result-panel">
				<div className="exam-tf-head exam-tf-result-head">
					<p>PHÁT BIỂU</p>
					<p>BẠN CHỌN</p>
					<p>ĐÁP ÁN</p>
				</div>

				{statements.map((statement, index) => {
					const studentToken = studentTokens[index] ?? '';
					const correctToken = correctTokens[index] ?? '';
					const isCorrect = studentToken === correctToken;

					return (
						<div key={`${question.question_id}-${index}`} className={`exam-tf-item exam-tf-result-item ${isCorrect ? 'is-correct' : 'is-wrong'}`}>
							<div className="exam-tf-statement">
								<span className="exam-tf-label">{getAlphabetLabel(index)}</span>
								<p><MathText text={statement} /></p>
							</div>
							<p className={`exam-tf-answer-chip ${isCorrect ? 'is-correct' : 'is-wrong'}`}>
								{studentToken ? tokenToLabel(studentToken) : 'Bỏ trống'}
							</p>
							<p className="exam-tf-answer-chip is-correct">{correctToken ? tokenToLabel(correctToken) : '-'}</p>
						</div>
					);
				})}
			</div>
		);
	}

	// Short-answer review only needs the submitted value and the correct answer.
	return (
		<div className="exam-short-wrap exam-result-panel">
			<div className={`exam-result-short ${evaluation.is_correct ? 'is-correct' : 'is-wrong'}`}>
				<p><strong>Bạn trả lời:</strong> {evaluation.student_answer || 'Bỏ trống'}</p>
				<p><strong>Đáp án đúng:</strong> {evaluation.correct_answer}</p>
			</div>
		</div>
	);
}
