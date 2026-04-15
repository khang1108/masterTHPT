export type StudentProfileLike = {
	name: string | null;
	grade: number | null;
	school: string | null;
	learning_goal: string | null;
};

export function hasCompletedProfile(student: StudentProfileLike) {
	return Boolean(
		student.name?.trim() &&
		typeof student.grade === 'number' &&
		student.grade >= 10 &&
		student.grade <= 12 &&
		student.school?.trim() &&
		student.learning_goal?.trim(),
	);
}
