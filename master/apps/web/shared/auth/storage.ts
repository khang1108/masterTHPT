import { Student } from '@/shared/models/student';

export const STORAGE_TOKEN_KEY = 'masterthpt_access_token';
export const STORAGE_STUDENT_KEY = 'masterthpt_student';

function normalizeStudent(value: unknown): Student | null {
	if (!value || typeof value !== 'object') {
		return null;
	}

	const candidate = value as Partial<Student> & {
		email?: unknown;
		id?: unknown;
	};
	if (typeof candidate.id !== 'string' || typeof candidate.email !== 'string') {
		return null;
	}

	return {
		id: candidate.id,
		email: candidate.email,
		name: typeof candidate.name === 'string' ? candidate.name : null,
		grade: typeof candidate.grade === 'number' ? candidate.grade : null,
		school: typeof candidate.school === 'string' ? candidate.school : null,
		learning_goal: typeof candidate.learning_goal === 'string' ? candidate.learning_goal : null,
		profile_completed: Boolean(candidate.profile_completed),
		is_first_login: Boolean(candidate.is_first_login),
	};
}

export function saveStudent(student: Student) {
	if (typeof window === 'undefined') {
		return;
	}

	const normalizedStudent = normalizeStudent(student);
	if (!normalizedStudent) {
		return;
	}

	localStorage.setItem(STORAGE_STUDENT_KEY, JSON.stringify(normalizedStudent));
}

export function saveAuth(token: string, student: Student) {
	if (typeof window === 'undefined') {
		return;
	}

	localStorage.setItem(STORAGE_TOKEN_KEY, token);
	saveStudent(student);
}

export function clearAuth() {
	if (typeof window === 'undefined') {
		return;
	}

	localStorage.removeItem(STORAGE_TOKEN_KEY);
	localStorage.removeItem(STORAGE_STUDENT_KEY);
}

export function getToken(): string | null {
	if (typeof window === 'undefined') {
		return null;
	}

	return localStorage.getItem(STORAGE_TOKEN_KEY);
}

export function getStudent(): Student | null {
	if (typeof window === 'undefined') {
		return null;
	}

	const raw = localStorage.getItem(STORAGE_STUDENT_KEY);
	if (!raw) {
		return null;
	}

	try {
		return normalizeStudent(JSON.parse(raw));
	} catch {
		return null;
	}
}

export function updateStudent(partial: Partial<Student>) {
	if (typeof window === 'undefined') {
		return;
	}

	const current = getStudent();
	if (!current) {
		return;
	}

	const normalizedStudent = normalizeStudent({
		...current,
		...partial,
	});
	if (!normalizedStudent) {
		return;
	}

	localStorage.setItem(STORAGE_STUDENT_KEY, JSON.stringify(normalizedStudent));
}
