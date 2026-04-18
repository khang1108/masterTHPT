import axios from 'axios';
import { Student } from '@/shared/models/student';

type LoginBody = {
	email: string;
	password: string;
};

type RegisterBody = {
	email: string;
	password: string;
	confirm_password: string;
};

type GoogleLoginBody = {
	credential: string;
};

export type LoginResponse = {
	access_token: string;
	student: Student;
};

export type RegisterResponse = {
	student: Student;
};

export type UpdateStudentProfileBody = {
	name: string;
	grade: 10 | 11 | 12;
	school: string;
	learning_goal: string;
};

export type DocumentItem = {
	id: string;
	title?: string;
	subject: string;
	grade: number;
	year: number;
	exam_type: string;
	type?: string;
	source?: string;
	total_questions?: number;
	duration?: number;
	created_at?: string;
	metadata?: unknown;
};

export type PracticeExamItem = {
	id: string;
	subject: string;
	source: string;
	total_questions: number;
	exam_type: string;
	grade: number;
	year: number;
};

export type UpdatePracticeBody = {
	request: string;
};

export type ExamQuestion = {
	question_id: string;
	question_index: number;
	type: 'multiple_choice' | 'true_false' | 'short_ans';
	content: string;
	options?: string[];
	statements?: string[];
	answer?: string;
	has_image: boolean;
	image_url?: string;
};

export type ExamSection = {
	type: 'multiple_choice' | 'true_false' | 'short_ans';
	section_name: string;
	questions: ExamQuestion[];
};

export type DocumentDetailResponse = {
	exam_id: string;
	source_type?: string;
	subject: string;
	grade?: number;
	exam_type: string;
	total_questions: number;
	duration_minutes: number;
	sections: ExamSection[];
};

export type GenerateOnboardingExamBody = {
	subject: 'Toán';
	grade: 10 | 11 | 12;
	exam_type: 'Giữa kì 1' | 'Cuối kì 1' | 'Giữa kì 2' | 'Cuối kì 2';
};

export type SubmitExamBody = {
	student_id: string;
	exam_id: string;
	time_taken_seconds: number;
	student_ans?: Array<{
		question_id: string;
		student_answer: string;
		time_spent_seconds?: number;
	}>;
	full_exam: {
		exam_id: string;
		subject: string;
		exam_type: string;
		total_questions: number;
		duration_minutes: number;
		sections: Array<{
			type: 'multiple_choice' | 'true_false' | 'short_ans';
			section_name: string;
			questions: Array<{
				question_id: string;
				question_index: number;
				type: 'multiple_choice' | 'true_false' | 'short_ans';
				content: string;
				content_latex?: string;
				options?: string[];
				statements?: string[];
				answer: string;
				student_answer: string;
				has_image?: boolean;
				image_url?: string;
				max_score?: number;
				difficulty_b?: number;
				topic_tags?: string[];
			}>;
		}>;
	};
};

export type ExamEvaluationItem = {
	question_id: string;
	student_answer: string;
	correct_answer: string;
	is_correct: boolean;
	reasoning: string;
	error_analysis: null | {
		error_type: string;
		remedial: string;
	};
};

export type ExamEvaluationResponse = {
	correct_count: number;
	total_questions: number;
	score: number | null;
	per_question: ExamEvaluationItem[];
};

export type PracticeQuestionCheckBody = {
	exam_id: string;
	question_id: string;
	student_answer: string;
};

export type PracticeQuestionCheckResponse = {
	question_id: string;
	student_answer: string;
	correct_answer: string;
	is_correct: boolean;
};

export type CreateHistoryBody = {
	intent: 'EXAM_PRACTICE' | 'VIEW_ANALYSIS';
	exam_id: string;
	student_ans: Array<{
		question_id: string;
		student_answer: string;
		time_spent_seconds?: number;
	}>;
	correct_count: number;
	score?: number;
};

export type HistoryListItem = {
	history_id: string;
	intent: 'EXAM_PRACTICE' | 'VIEW_ANALYSIS';
	exam_id: string;
	correct_count: number;
	score?: number | null;
	created_at: string;
	subject: string;
	grade: number | null;
	exam_type: string;
	source: string;
	total_questions: number;
	duration: number;
	year: number | null;
};

export type HistoryDetailResponse = {
	history_id: string;
	intent: 'EXAM_PRACTICE' | 'VIEW_ANALYSIS';
	correct_count: number;
	score?: number | null;
	created_at: string;
	exam_id: string;
	subject: string;
	grade: number;
	exam_type: string;
	source: string;
	total_questions: number;
	duration_minutes: number;
	sections: ExamSection[];
	evaluation: ExamEvaluationResponse;
};

export type AskHintBody = {
	exam_id: string;
	question_id: string;
};

export type AskHintResponse = {
	user_id: string;
	exam_id: string;
	question_id: string;
	feedback: string;
};

export type ReviewMistakeBody = {
	question_id: string;
	student_ans: string;
};

export type ReviewMistakeResponse = {
	user_id: string;
	question_id: string;
	feedback: string;
};

const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL?.trim() || '/api';

const api = axios.create({
	baseURL: apiBaseUrl,
	timeout: 60000,
});

export async function login(body: LoginBody) {
	const { data } = await api.post<LoginResponse>('/auth/login', body);
	return data;
}

export async function loginWithGoogle(body: GoogleLoginBody) {
	const { data } = await api.post<LoginResponse>('/auth/google', body);
	return data;
}

export async function register(body: RegisterBody) {
	const { data } = await api.post<RegisterResponse>('/auth/register', body);
	return data;
}

export async function getCurrentStudent(token: string) {
	const { data } = await api.get<Student>('/students/me', {
		headers: {
			Authorization: `Bearer ${token}`,
		},
	});

	return data;
}

export async function updateCurrentStudent(token: string, body: UpdateStudentProfileBody) {
	const { data } = await api.patch<Student>('/students/me', body, {
		headers: {
			Authorization: `Bearer ${token}`,
		},
	});

	return data;
}

export async function getDocuments(token: string) {
	const { data } = await api.get<DocumentItem[]>('/documents', {
		headers: {
			Authorization: `Bearer ${token}`,
		},
	});
	return data;
}

export async function getPracticeExams(token: string) {
	const { data } = await api.get<PracticeExamItem[]>('/practice', {
		headers: {
			Authorization: `Bearer ${token}`,
		},
	});

	return data;
}

export async function updatePractice(token: string, body: UpdatePracticeBody) {
	const { data } = await api.post('/practice/update', body, {
		headers: {
			Authorization: `Bearer ${token}`,
		},
	});

	return data;
}

export async function getDocumentDetail(id: string, token: string) {
	const { data } = await api.get<DocumentDetailResponse>(`/documents/${id}`, {
		headers: {
			Authorization: `Bearer ${token}`,
		},
	});
	return data;
}

export async function generateOnboardingExam(
	token: string,
	body: GenerateOnboardingExamBody,
) {
	const { data } = await api.post<DocumentDetailResponse>('/onboarding/exam', body, {
		headers: {
			Authorization: `Bearer ${token}`,
		},
	});

	return data;
}

export async function submitExam(token: string, body: SubmitExamBody) {
	const { data } = await api.post<ExamEvaluationResponse>('/exams/submit', body, {
		headers: {
			Authorization: `Bearer ${token}`,
		},
	});

	return data;
}

export async function checkPracticeQuestion(token: string, body: PracticeQuestionCheckBody) {
	const { data } = await api.post<PracticeQuestionCheckResponse>('/practice/check-question', body, {
		headers: {
			Authorization: `Bearer ${token}`,
		},
	});

	return data;
}

export async function createHistory(token: string, body: CreateHistoryBody) {
	const { data } = await api.post('/history', body, {
		headers: {
			Authorization: `Bearer ${token}`,
		},
	});

	return data;
}

export async function getHistoryList(token: string) {
	const { data } = await api.get<HistoryListItem[]>('/history', {
		headers: {
			Authorization: `Bearer ${token}`,
		},
	});

	return data;
}

export async function getHistoryDetail(id: string, token: string) {
	const { data } = await api.get<HistoryDetailResponse>(`/history/${id}`, {
		headers: {
			Authorization: `Bearer ${token}`,
		},
	});

	return data;
}

export async function askHint(token: string, body: AskHintBody) {
	const { data } = await api.post<AskHintResponse>('/hints', body, {
		headers: {
			Authorization: `Bearer ${token}`,
		},
	});

	return data;
}

export async function reviewMistake(token: string, body: ReviewMistakeBody) {
	const { data } = await api.post<ReviewMistakeResponse>('/hints/review-mistake', body, {
		headers: {
			Authorization: `Bearer ${token}`,
		},
	});

	return data;
}
