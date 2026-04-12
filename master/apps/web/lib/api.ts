import axios from 'axios';

type LoginBody = {
	email: string;
	password: string;
};

type RegisterBody = {
	name: string;
	email: string;
	password: string;
	grade: number;
};

type Student = {
	id: string;
	name: string;
	email: string;
	grade: number;
	is_first_login: boolean;
};

export type LoginResponse = {
	access_token: string;
	student: Student;
};

export type RegisterResponse = {
	student: Student;
};

export type DocumentItem = {
	id: string;
	title: string;
	subject: string;
	year: number;
	exam_type: string;
	type: string;
};

export type ExamQuestion = {
	id: string;
	question_index: number;
	type: 'multiple_choice' | 'true_false' | 'short_answer';
	content: string;
	options?: string[];
	statements?: string[];
	answer?: string;
	correct_answer?: string;
	has_image: boolean;
	image_url?: string;
};

export type ExamSection = {
	type: 'multiple_choice' | 'true_false' | 'short_answer';
	section_name: string;
	questions: ExamQuestion[];
};

export type DocumentDetailResponse = {
	exam_id: string;
	source_type?: string;
	subject: string;
	exam_type: string;
	total_questions: number;
	duration_minutes: number;
	sections: ExamSection[];
};

export type GeneratePracticeBody = {
	embedded_text?: string;
	subject?: string;
	exam_type?: string;
	file?: File;
};

export type OnboardingSubjectScore = {
	label: string;
	value: string;
};

export type OnboardingSubject = {
	subject: string;
	scores: OnboardingSubjectScore[];
};

export type GenerateOnboardingExamBody = {
	subjects: OnboardingSubject[];
};

export type SubmitExamBody = {
	student_id: string;
	exam_id: string;
	time_taken_seconds: number;
	full_exam: {
		exam_id: string;
		subject: string;
		exam_type: string;
		total_questions: number;
		duration_minutes: number;
		sections: Array<{
			type: 'multiple_choice' | 'true_false' | 'short_answer';
			section_name: string;
			questions: Array<{
				id: string;
				question_index: number;
				type: 'multiple_choice' | 'true_false' | 'short_answer';
				content: string;
				content_latex?: string;
				options?: string[];
				statements?: string[];
				correct_answer?: string;
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
	score: number;
	max_score: number;
	reasoning: string;
	error_analysis: null | {
		error_type: string;
		remedial: string;
	};
};

export type ExamEvaluationResponse = {
	total_score: number;
	max_score: number;
	overall_analysis: {
		strengths: string[];
		weaknesses: string[];
		general_advice: string;
	};
	per_question: ExamEvaluationItem[];
};

const api = axios.create({
	baseURL: '/api',
	timeout: 12000,
});

export async function login(body: LoginBody) {
	const { data } = await api.post<LoginResponse>('/auth/login', body);
	return data;
}

export async function register(body: RegisterBody) {
	const { data } = await api.post<RegisterResponse>('/auth/register', body);
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

export async function getDocumentDetail(id: string, token: string) {
	const { data } = await api.get<DocumentDetailResponse>(`/documents/${id}`, {
		headers: {
			Authorization: `Bearer ${token}`,
		},
	});
	return data;
}

export async function generatePractice(token: string, body: GeneratePracticeBody) {
	const formData = new FormData();

	if (body.file) {
		formData.append('file', body.file);
	}

	if (body.embedded_text && body.embedded_text.trim().length > 0) {
		formData.append('embedded_text', body.embedded_text.trim());
	}

	if (body.subject && body.subject.trim().length > 0) {
		formData.append('subject', body.subject.trim());
	}

	if (body.exam_type && body.exam_type.trim().length > 0) {
		formData.append('exam_type', body.exam_type.trim());
	}

	const { data } = await api.post<DocumentDetailResponse>('/practice/generate', formData, {
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
	const { data } = await api.post<DocumentDetailResponse>('/practice/onboarding', body, {
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
