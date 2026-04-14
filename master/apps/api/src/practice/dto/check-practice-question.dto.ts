import { IsNotEmpty, IsString } from 'class-validator';

export class CheckPracticeQuestionDto {
	@IsString()
	@IsNotEmpty()
	exam_id: string;

	@IsString()
	@IsNotEmpty()
	question_id: string;

	@IsString()
	student_answer: string;
}
