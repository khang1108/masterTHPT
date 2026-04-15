import { Student } from '@/shared/models/student';

export const GRADE_OPTIONS = [10, 11, 12] as const;

export type StudentGrade = (typeof GRADE_OPTIONS)[number];

export type StudentProfileFormValue = {
	name: string;
	grade: StudentGrade;
	school: string;
	learning_goal: string;
};

export function createStudentProfileDraft(student?: Student | null): StudentProfileFormValue {
	return {
		name: student?.name ?? '',
		grade: student?.grade && student.grade >= 10 && student.grade <= 12 ? student.grade as StudentGrade : 12,
		school: student?.school ?? '',
		learning_goal: student?.learning_goal ?? '',
	};
}

export function getStudentDisplayName(student: Pick<Student, 'name' | 'email'>) {
	const trimmedName = student.name?.trim();
	if (trimmedName) {
		return trimmedName;
	}

	const fallback = student.email.split('@')[0]?.trim();
	return fallback || 'Học sinh';
}

export function getStudentInitials(student: Pick<Student, 'name' | 'email'>) {
	const displayName = getStudentDisplayName(student);
	const tokens = displayName.split(/\s+/).filter(Boolean);
	if (tokens.length === 0) {
		return 'HS';
	}

	if (tokens.length === 1) {
		return tokens[0].slice(0, 2).toUpperCase();
	}

	return `${tokens[0][0] ?? ''}${tokens[tokens.length - 1][0] ?? ''}`.toUpperCase();
}
