import { IsOptional, IsString } from 'class-validator';

export class GeneratePracticeDto {
	@IsOptional()
	@IsString()
	embedded_text?: string;

	@IsOptional()
	@IsString()
	subject?: string;

	@IsOptional()
	@IsString()
	exam_type?: string;
}
