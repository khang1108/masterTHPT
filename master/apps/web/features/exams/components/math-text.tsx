import Latex from 'react-latex-next';

// All math-capable text goes through one component so we can swap rendering strategy later
// without updating every screen individually.
export function MathText({ text }: { text: string }) {
	return (
		<span className="exam-math-text">
			<Latex>{text}</Latex>
		</span>
	);
}
