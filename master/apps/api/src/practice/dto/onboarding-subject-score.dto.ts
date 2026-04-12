import { IsNotEmpty, IsString, MaxLength } from 'class-validator';

export class OnboardingSubjectScoreDto {
	@IsString()
	@IsNotEmpty()
	@MaxLength(100)
	label: string;

	@IsString()
	@IsNotEmpty()
	@MaxLength(40)
	value: string;
}
