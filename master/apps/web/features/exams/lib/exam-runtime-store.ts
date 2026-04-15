import { DocumentDetailResponse, ExamEvaluationResponse } from '@/shared/api/client';

export type ExamQuestionTimingMap = Record<string, number>;

type ExamRuntimeStore = {
	details: Map<string, DocumentDetailResponse>;
	results: Map<string, ExamEvaluationResponse>;
	timings: Map<string, ExamQuestionTimingMap>;
};

const examRuntimeStore: ExamRuntimeStore = {
	details: new Map<string, DocumentDetailResponse>(),
	results: new Map<string, ExamEvaluationResponse>(),
	timings: new Map<string, ExamQuestionTimingMap>(),
};

function cloneValue<T>(value: T): T {
	if (typeof structuredClone === 'function') {
		return structuredClone(value);
	}

	return JSON.parse(JSON.stringify(value)) as T;
}

function getCachedValue<T>(store: Map<string, T>, examId: string): T | null {
	const value = store.get(examId);
	if (!value) {
		return null;
	}

	return cloneValue(value);
}

function setCachedValue<T>(store: Map<string, T>, examId: string, value: T) {
	store.set(examId, cloneValue(value));
}

export function cacheExamDetail(exam: DocumentDetailResponse) {
	setCachedValue(examRuntimeStore.details, exam.exam_id, exam);
}

export function getCachedExamDetail(examId: string): DocumentDetailResponse | null {
	return getCachedValue(examRuntimeStore.details, examId);
}

export function cacheExamResult(examId: string, result: ExamEvaluationResponse) {
	setCachedValue(examRuntimeStore.results, examId, result);
}

export function getCachedExamResult(examId: string): ExamEvaluationResponse | null {
	return getCachedValue(examRuntimeStore.results, examId);
}

export function cacheExamQuestionTimings(examId: string, timings: ExamQuestionTimingMap) {
	setCachedValue(examRuntimeStore.timings, examId, timings);
}

export function getCachedExamQuestionTimings(examId: string): ExamQuestionTimingMap {
	return getCachedValue(examRuntimeStore.timings, examId) ?? {};
}

export function clearCachedExamDetail(examId: string) {
	examRuntimeStore.details.delete(examId);
}

export function clearCachedExamResult(examId: string) {
	examRuntimeStore.results.delete(examId);
}

export function clearCachedExamQuestionTimings(examId: string) {
	examRuntimeStore.timings.delete(examId);
}

export function clearExamRuntimeCache(examId: string) {
	clearCachedExamDetail(examId);
	clearCachedExamResult(examId);
	clearCachedExamQuestionTimings(examId);
}
