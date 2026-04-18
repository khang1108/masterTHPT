import { Prisma } from '@prisma/client';

type StudentAnswerRecord = {
	question_id: string;
	student_answer: string;
};

type QuestionAnswer = {
	question_id: string;
	type?: string | null;
	correct_answer?: string | null;
};

const TRUE_FALSE_SCORE_BY_MATCH_COUNT: Record<number, number> = {
	0: 0,
	1: 0.1,
	2: 0.25,
	3: 0.5,
};

function roundScore(value: number) {
	return Math.round(value * 100) / 100;
}

function normalizeAnswerTokens(value?: string | null) {
	return normalizeComparableAnswer(value)
		.split(',')
		.map((token) => token.trim());
}

function countTrueFalseMatches(studentAnswer?: string | null, correctAnswer?: string | null) {
	if (normalizeComparableAnswer(correctAnswer).length === 0) {
		return 0;
	}

	const studentTokens = normalizeAnswerTokens(studentAnswer);
	const correctTokens = normalizeAnswerTokens(correctAnswer);
	const tokenCount = Math.max(studentTokens.length, correctTokens.length);

	let matchedStatements = 0;
	for (let index = 0; index < tokenCount; index += 1) {
		if ((studentTokens[index] ?? '') === (correctTokens[index] ?? '')) {
			matchedStatements += 1;
		}
	}

	return matchedStatements;
}

function getTrueFalseQuestionScore(studentAnswer?: string | null, correctAnswer?: string | null) {
	const matchedStatements = countTrueFalseMatches(studentAnswer, correctAnswer);

	if (matchedStatements >= 4) {
		return 1;
	}

	return TRUE_FALSE_SCORE_BY_MATCH_COUNT[matchedStatements] ?? 0;
}

function getQuestionScore(question: QuestionAnswer, studentAnswer?: string | null) {
	switch (question.type) {
		case 'multiple_choice':
			return isAnswerCorrect(studentAnswer, question.correct_answer) ? 0.25 : 0;
		case 'short_ans':
			return isAnswerCorrect(studentAnswer, question.correct_answer) ? 0.5 : 0;
		case 'true_false':
			return getTrueFalseQuestionScore(studentAnswer, question.correct_answer);
		default:
			return 0;
	}
}

export function normalizeComparableAnswer(value?: string | null) {
	// Answer comparison is intentionally case-insensitive and whitespace-insensitive
	// so submit, practice-check, and history review all grade with the same rule.
	return (value ?? '').trim().toUpperCase();
}

export function isAnswerCorrect(studentAnswer?: string | null, correctAnswer?: string | null) {
	return normalizeComparableAnswer(studentAnswer) === normalizeComparableAnswer(correctAnswer);
}

export function normalizeHistoryStudentAnswers(raw: Prisma.JsonValue): StudentAnswerRecord[] {
	if (!Array.isArray(raw)) {
		return [];
	}

	// Histories store answers as JSON, so we normalize the shape before rebuilding
	// review data. This lets the read path stay resilient if older records are imperfect.
	return raw.flatMap((item) => {
		if (!item || typeof item !== 'object' || Array.isArray(item)) {
			return [];
		}

		const questionId = item.question_id;
		const studentAnswer = item.student_answer;

		if (typeof questionId !== 'string' || typeof studentAnswer !== 'string') {
			return [];
		}

		return [{
			question_id: questionId,
			student_answer: studentAnswer,
		}];
	});
}

export function buildEvaluationFromAnswerMap(
	questions: QuestionAnswer[],
	answerMap: Map<string, string>,
) {
	// Reuse the same comparison rules everywhere so exam submit, review, and practice stay consistent.
	const per_question = questions.map((question) => {
		const studentAnswer = (answerMap.get(question.question_id) ?? '').trim();
		const correctAnswer = (question.correct_answer ?? '').trim();

		return {
			question_id: question.question_id,
			student_answer: studentAnswer,
			correct_answer: correctAnswer,
			is_correct: isAnswerCorrect(studentAnswer, correctAnswer),
			reasoning: '',
			error_analysis: null,
		};
	});

	const score = roundScore(
		questions.reduce((sum, question) => (
			sum + getQuestionScore(question, answerMap.get(question.question_id) ?? '')
		), 0),
	);

	return {
		correct_count: per_question.filter((item) => item.is_correct).length,
		total_questions: questions.length,
		score,
		per_question,
	};
}
