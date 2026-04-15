import { IsInt, IsNotEmpty, IsString, Max, Min } from 'class-validator';

export class UpdateStudentProfileDto {
	@IsString()
	@IsNotEmpty()
	name: string;

	@IsInt()
	@Min(10)
	@Max(12)
	grade: number;

	@IsString()
	@IsNotEmpty()
	school: string;

	@IsString()
	@IsNotEmpty()
	learning_goal: string;
}
