import { Type } from 'class-transformer';
import {
	ArrayNotEmpty,
	IsArray,
	IsBoolean,
	IsInt,
	IsNotEmpty,
	IsNumber,
	IsOptional,
	IsString,
	ValidateNested,
} from 'class-validator';

class SubmittedExamQuestionSnapshotDto {
	@IsString()
	@IsNotEmpty()
	id: string;

	@IsInt()
	question_index: number;

	@IsString()
	type: string;

	@IsString()
	@IsNotEmpty()
	content: string;

	@IsOptional()
	@IsArray()
	options?: string[];

	@IsOptional()
	@IsArray()
	statements?: string[];

	@IsOptional()
	@IsString()
	content_latex?: string;

	@IsOptional()
	@IsString()
	correct_answer?: string;

	@IsString()
	answer: string;

	@IsString()
	student_answer: string;

	@IsOptional()
	@IsBoolean()
	has_image?: boolean;

	@IsOptional()
	@IsString()
	image_url?: string;

	@IsOptional()
	@IsNumber()
	max_score?: number;

	@IsOptional()
	@IsNumber()
	difficulty_b?: number;

	@IsOptional()
	@IsArray()
	topic_tags?: string[];
}

class SubmittedExamSectionSnapshotDto {
	@IsString()
	type: string;

	@IsString()
	section_name: string;

	@IsArray()
	@ValidateNested({ each: true })
	@Type(() => SubmittedExamQuestionSnapshotDto)
	questions: SubmittedExamQuestionSnapshotDto[];
}

class SubmittedExamSnapshotDto {
	@IsString()
	@IsNotEmpty()
	exam_id: string;

	@IsOptional()
	@IsString()
	source?: string;

	@IsString()
	@IsNotEmpty()
	subject: string;

	@IsString()
	@IsNotEmpty()
	exam_type: string;

	@IsInt()
	total_questions: number;

	@IsInt()
	duration_minutes: number;

	@IsArray()
	@ArrayNotEmpty()
	@ValidateNested({ each: true })
	@Type(() => SubmittedExamSectionSnapshotDto)
	sections: SubmittedExamSectionSnapshotDto[];
}

export class SubmitExamDto {
	@IsString()
	student_id: string;

	@IsString()
	exam_id: string;

	@IsInt()
	time_taken_seconds: number;

	@ValidateNested()
	@Type(() => SubmittedExamSnapshotDto)
	full_exam: SubmittedExamSnapshotDto;
}
