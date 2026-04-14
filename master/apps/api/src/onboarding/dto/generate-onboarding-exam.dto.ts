import { IsIn, IsInt, IsString, Max, Min } from 'class-validator';

export class GenerateOnboardingExamDto {
	@IsString()
	@IsIn(['Toán'])
	subject: string;

	@IsInt()
	@Min(10)
	@Max(12)
	grade: number;

	@IsString()
	@IsIn(['Giữa kì 1', 'Cuối kì 1', 'Giữa kì 2', 'Cuối kì 2'])
	exam_type: string;
}
