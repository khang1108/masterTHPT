import { Type } from 'class-transformer';
import { ArrayMinSize, IsArray, IsIn, IsInt, IsNotEmpty, IsNumber, IsOptional, IsString, Min, ValidateNested } from 'class-validator';

export class HistoryStudentAnswerDto {
	@IsString()
	@IsNotEmpty()
	question_id: string;

	@IsString()
	student_answer: string;

	@IsOptional()
	@IsInt()
	@Min(0)
	time_spent_seconds?: number;
}

export class CreateHistoryDto {
	@IsString()
	@IsIn(['EXAM_PRACTICE', 'VIEW_ANALYSIS'])
	intent: 'EXAM_PRACTICE' | 'VIEW_ANALYSIS';

	@IsString()
	@IsNotEmpty()
	exam_id: string;

	@IsArray()
	@ArrayMinSize(1)
	@ValidateNested({ each: true })
	@Type(() => HistoryStudentAnswerDto)
	student_ans: HistoryStudentAnswerDto[];

	@IsInt()
	@Min(0)
	correct_count: number;

	@IsOptional()
	@IsNumber()
	@Min(0)
	score?: number;
}
