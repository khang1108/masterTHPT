export function parseOption(option: string) {
	const match = option.match(/^([A-Z])\.\s*(.*)$/);
	if (!match) {
		return {
			label: option,
			text: option,
		};
	}

	return {
		label: match[1],
		text: match[2],
	};
}

export function getAlphabetLabel(index: number) {
	return String.fromCharCode(65 + index);
}

export function tokenToLabel(value: string) {
	return value === 'T' ? 'Đúng' : 'Sai';
}

export function formatDateTime(value: string) {
	const date = new Date(value);
	if (Number.isNaN(date.getTime())) {
		return value;
	}

	return new Intl.DateTimeFormat('vi-VN', {
		dateStyle: 'short',
		timeStyle: 'short',
	}).format(date);
}

export function formatScore(value: number) {
	return new Intl.NumberFormat('vi-VN', {
		minimumFractionDigits: 0,
		maximumFractionDigits: 2,
	}).format(value);
}
