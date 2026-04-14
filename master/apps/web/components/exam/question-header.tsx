type ExamQuestionHeaderProps = {
	questionIndex: number;
	showHintButton?: boolean;
	onAskHint: () => void;
	isHintLoading: boolean;
	hasHint: boolean;
	showReviewButton?: boolean;
	onReviewMistake?: () => void;
	isReviewLoading?: boolean;
	hasReview?: boolean;
	statusText?: string;
	statusTone?: 'is-correct' | 'is-wrong';
};

// This header is shared by exam, result, and history-review screens so button placement
// stays consistent when we add more per-question actions later.
export function ExamQuestionHeader({
	questionIndex,
	showHintButton = true,
	onAskHint,
	isHintLoading,
	hasHint,
	showReviewButton = false,
	onReviewMistake,
	isReviewLoading = false,
	hasReview = false,
	statusText,
	statusTone,
}: ExamQuestionHeaderProps) {
	return (
		<div className="exam-question-top">
			<div className="exam-question-chip">
				<span>{questionIndex}</span>
				<strong>CÂU {questionIndex}</strong>
			</div>
			<div className="exam-question-actions">
				{showHintButton ? (
					<button
						type="button"
						className="exam-hint-btn"
						onClick={onAskHint}
						disabled={isHintLoading || hasHint}
					>
						{/* Hint is intentionally one-shot per question in the current product flow. */}
						{isHintLoading ? 'Đang lấy gợi ý...' : hasHint ? 'Đã lấy gợi ý' : 'Gợi ý'}
					</button>
				) : null}
				{showReviewButton && onReviewMistake ? (
					<button
						type="button"
						className="exam-review-btn"
						onClick={onReviewMistake}
						disabled={isReviewLoading || hasReview}
					>
						{/* Review is also one-shot so users do not repeatedly call the AI endpoint. */}
						{isReviewLoading ? 'Đang lấy giải thích...' : hasReview ? 'Đã lấy giải thích' : 'Giải thích'}
					</button>
				) : null}
				{statusText && statusTone ? (
					<p className={`exam-result-status ${statusTone}`}>
						{statusText}
					</p>
				) : null}
			</div>
		</div>
	);
}
