import { MathText } from '@/components/exam/math-text';
import { getAlphabetLabel, parseOption } from '@/components/exam/helpers';
import { FlatQuestion } from '@/components/exam/types';

type EditableAnswerPanelProps = {
	question: FlatQuestion;
	answer: string;
	onChange: (value: string) => void;
	disabled?: boolean;
};

// Keep each answer type isolated here so future question formats can be added
// without making the page-level containers harder to follow.
export function EditableAnswerPanel({
	question,
	answer,
	onChange,
	disabled = false,
}: EditableAnswerPanelProps) {
	if (question.sectionType === 'multiple_choice') {
		return (
			<div className="exam-mc-grid">
				{question.question.options?.map((option) => {
					// Options currently come from the API in "A. ..." shape.
					// Parsing is centralized so we only need to change it in one place later.
					const parsed = parseOption(option);
					const isSelected = answer === parsed.label;

					return (
						<button
							key={`${question.id}-${parsed.label}`}
							type="button"
							className={`exam-mc-option ${isSelected ? 'is-selected' : ''}`}
							onClick={() => onChange(parsed.label)}
							disabled={disabled}
						>
							<div className="exam-mc-option-main">
								<span className="exam-mc-badge">{parsed.label}</span>
								<MathText text={parsed.text} />
							</div>
							<span className="exam-mc-tail">{parsed.label}</span>
						</button>
					);
				})}
			</div>
		);
	}

	if (question.sectionType === 'true_false') {
		const statements = question.question.statements ?? [];
		const tokens = answer.split(',');

		return (
			<div className="exam-tf-table">
				<div className="exam-tf-head">
					<p>PHÁT BIỂU</p>
					<p>ĐÚNG</p>
					<p>SAI</p>
				</div>

				{statements.map((statement, index) => {
					const current = tokens[index] ?? '';

					function updateToken(next: 'T' | 'F') {
						// Keep the comma-delimited answer format unchanged for the current API contract.
						const clone = [...tokens];
						clone[index] = next;
						onChange(clone.join(','));
					}

					return (
						<div key={`${question.id}-${index}`} className="exam-tf-item">
							<div className="exam-tf-statement">
								<span className="exam-tf-label">{getAlphabetLabel(index)}</span>
								<p><MathText text={statement} /></p>
							</div>

							<button
								type="button"
								className={`exam-tf-radio ${current === 'T' ? 'is-selected' : ''}`}
								onClick={() => updateToken('T')}
								aria-label={`Chọn đúng cho phát biểu ${getAlphabetLabel(index)}`}
								disabled={disabled}
							/>
							<button
								type="button"
								className={`exam-tf-radio ${current === 'F' ? 'is-selected' : ''}`}
								onClick={() => updateToken('F')}
								aria-label={`Chọn sai cho phát biểu ${getAlphabetLabel(index)}`}
								disabled={disabled}
							/>
						</div>
					);
				})}
			</div>
		);
	}

	// Short-answer remains a plain text field for now.
	// If we later support richer math input, this is the only branch that needs to evolve.
	return (
		<div className="exam-short-wrap">
			<input
				type="text"
				className="exam-short-input"
				placeholder=""
				value={answer}
				onChange={(event) => onChange(event.target.value)}
				disabled={disabled}
			/>
		</div>
	);
}
