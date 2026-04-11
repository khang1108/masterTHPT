import { Type } from 'class-transformer';
import { ArrayMinSize, IsArray, IsNotEmpty, IsString, MaxLength, ValidateNested } from 'class-validator';
import { OnboardingSubjectScoreDto } from './onboarding-subject-score.dto';

export class OnboardingSubjectDto {
	@IsString()
	@IsNotEmpty()
	@MaxLength(100)
	subject: string;

	@IsArray()
	@ArrayMinSize(1)
	@ValidateNested({ each: true })
	@Type(() => OnboardingSubjectScoreDto)
	scores: OnboardingSubjectScoreDto[];
}
