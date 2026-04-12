export const STORAGE_TOKEN_KEY = 'masterthpt_access_token';
export const STORAGE_STUDENT_KEY = 'masterthpt_student';

type Student = {
	id: string;
	name: string;
	email: string;
	grade: number;
	is_first_login: boolean;
};

export function saveAuth(token: string, student: Student) {
	if (typeof window === 'undefined') {
		return;
	}

	localStorage.setItem(STORAGE_TOKEN_KEY, token);
	localStorage.setItem(STORAGE_STUDENT_KEY, JSON.stringify(student));
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
		return JSON.parse(raw) as Student;
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

	localStorage.setItem(
		STORAGE_STUDENT_KEY,
		JSON.stringify({
			...current,
			...partial,
		}),
	);
}
