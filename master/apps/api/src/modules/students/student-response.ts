import { Student } from '@prisma/client';
import { hasCompletedProfile } from './student-profile-state';

export type StudentResponse = {
	id: string;
	name: string | null;
	email: string;
	grade: number | null;
	school: string | null;
	learning_goal: string | null;
	profile_completed: boolean;
	is_first_login: boolean;
};

export function toStudentResponse(student: Student): StudentResponse {
	return {
		id: student.user_id,
		name: student.name,
		email: student.email,
		grade: student.grade,
		school: student.school,
		learning_goal: student.learning_goal,
		profile_completed: Boolean(student.profile_completed) || hasCompletedProfile(student),
		is_first_login: student.is_first_login,
	};
}
