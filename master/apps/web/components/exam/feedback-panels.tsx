import { MathText } from '@/components/exam/math-text';

type QuestionFeedbackPanelsProps = {
	hintError?: string;
	hintFeedback?: string;
	reviewError?: string;
	reviewFeedback?: string;
};

export function QuestionFeedbackPanels({
	hintError,
	hintFeedback,
	reviewError,
	reviewFeedback,
}: QuestionFeedbackPanelsProps) {
	return (
		<>
			{hintError ? <p className="documents-error exam-submit-error">{hintError}</p> : null}
			{hintFeedback ? (
				<div className="exam-hint-box">
					<p className="exam-hint-title">Gợi ý từ AI</p>
					<div className="exam-hint-content">
						<MathText text={hintFeedback} />
					</div>
				</div>
			) : null}

			{reviewError ? <p className="documents-error exam-submit-error">{reviewError}</p> : null}
			{reviewFeedback ? (
				<div className="exam-review-box">
					<p className="exam-review-title">Giải thích từ AI</p>
					<div className="exam-review-content">
						<MathText text={reviewFeedback} />
					</div>
				</div>
			) : null}
		</>
	);
}
