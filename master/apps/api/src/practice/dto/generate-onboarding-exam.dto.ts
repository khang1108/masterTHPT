import { Type } from 'class-transformer';
import { ArrayMinSize, IsArray, ValidateNested } from 'class-validator';
import { OnboardingSubjectDto } from './onboarding-subject.dto';

export class GenerateOnboardingExamDto {
	@IsArray()
	@ArrayMinSize(1)
	@ValidateNested({ each: true })
	@Type(() => OnboardingSubjectDto)
	subjects: OnboardingSubjectDto[];
}
