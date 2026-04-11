import { DocumentDetailResponse, ExamEvaluationResponse } from './api';

const EXAM_SESSION_PREFIX = 'masterthpt_exam_';
const EXAM_RESULT_SESSION_PREFIX = 'masterthpt_exam_result_';

function getStorageKey(examId: string) {
	return `${EXAM_SESSION_PREFIX}${examId}`;
}

function getResultStorageKey(examId: string) {
	return `${EXAM_RESULT_SESSION_PREFIX}${examId}`;
}

export function cacheExamDetail(exam: DocumentDetailResponse) {
	if (typeof window === 'undefined') {
		return;
	}

	try {
		window.sessionStorage.setItem(getStorageKey(exam.exam_id), JSON.stringify(exam));
	} catch {
		// Ignore storage write failure to keep UX uninterrupted.
	}
}

export function getCachedExamDetail(examId: string): DocumentDetailResponse | null {
	if (typeof window === 'undefined') {
		return null;
	}

	try {
		const raw = window.sessionStorage.getItem(getStorageKey(examId));
		if (!raw) {
			return null;
		}

		return JSON.parse(raw) as DocumentDetailResponse;
	} catch {
		return null;
	}
}

export function cacheExamResult(examId: string, result: ExamEvaluationResponse) {
	if (typeof window === 'undefined') {
		return;
	}

	try {
		window.sessionStorage.setItem(getResultStorageKey(examId), JSON.stringify(result));
	} catch {
		// Ignore storage write failure to keep UX uninterrupted.
	}
}

export function getCachedExamResult(examId: string): ExamEvaluationResponse | null {
	if (typeof window === 'undefined') {
		return null;
	}

	try {
		const raw = window.sessionStorage.getItem(getResultStorageKey(examId));
		if (!raw) {
			return null;
		}

		return JSON.parse(raw) as ExamEvaluationResponse;
	} catch {
		return null;
	}
}
