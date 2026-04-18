import { useEffect, useMemo, useState } from 'react';
import { MathText } from '@/features/exams/components/math-text';
import { AskHintLevels } from '@/shared/api/client';

type QuestionFeedbackPanelsProps = {
	hintError?: string;
	hintFeedback?: string;
	hintLevels?: AskHintLevels;
	reviewError?: string;
	reviewFeedback?: string;
};

function hasHintLevels(levels?: AskHintLevels) {
	if (!levels) {
		return false;
	}

	return Boolean(levels.hint_1 || levels.hint_2 || levels.hint_3);
}

type HintLevelItem = {
	key: keyof AskHintLevels;
	label: string;
	content: string;
};

export function QuestionFeedbackPanels({
	hintError,
	hintFeedback,
	hintLevels,
	reviewError,
	reviewFeedback,
}: QuestionFeedbackPanelsProps) {
	const hasStructuredHints = hasHintLevels(hintLevels);
	const hintItems = useMemo<HintLevelItem[]>(() => {
		if (!hintLevels) {
			return [];
		}

		return [
			{ key: 'hint_1', label: 'Hint 1', content: hintLevels.hint_1 },
			{ key: 'hint_2', label: 'Hint 2', content: hintLevels.hint_2 },
			{ key: 'hint_3', label: 'Hint 3', content: hintLevels.hint_3 },
		].filter((item) => item.content);
	}, [hintLevels]);
	const [expandedHints, setExpandedHints] = useState<Record<string, boolean>>({});

	useEffect(() => {
		// Reset trạng thái mở mỗi khi bộ hint đổi sang câu hỏi khác, để UI luôn
		// bắt đầu ở trạng thái "đã có các hint, nhưng chưa xổ nội dung".
		setExpandedHints({});
	}, [hintFeedback, hintLevels]);

	const toggleHint = (key: string) => {
		setExpandedHints((prev) => ({
			...prev,
			[key]: !prev[key],
		}));
	};

	return (
		<>
			{hintError ? <p className="documents-error exam-submit-error">{hintError}</p> : null}
			{hasStructuredHints ? (
				<div className="exam-hint-box">
					<p className="exam-hint-title">Gợi ý từ AI</p>
					<div className="exam-hint-level-list">
						{hintItems.map((item) => {
							const isExpanded = Boolean(expandedHints[item.key]);

							return (
								<div className="exam-hint-level" key={item.key}>
									<button
										type="button"
										className={`exam-hint-level-toggle ${isExpanded ? 'is-expanded' : ''}`}
										onClick={() => toggleHint(item.key)}
										aria-expanded={isExpanded}
									>
										<span className="exam-hint-level-title">{item.label}</span>
										<span className="exam-hint-level-toggle-icon" aria-hidden="true">
											{isExpanded ? '−' : '+'}
										</span>
									</button>
									{isExpanded ? (
										<div className="exam-hint-content">
											<MathText text={item.content} />
										</div>
									) : null}
								</div>
							);
						})}
					</div>
				</div>
			) : hintFeedback ? (
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
