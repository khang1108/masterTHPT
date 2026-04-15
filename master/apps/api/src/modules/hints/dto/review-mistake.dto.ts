import { IsNotEmpty, IsString } from 'class-validator';

export class ReviewMistakeDto {
	@IsString()
	@IsNotEmpty()
	question_id: string;

	@IsString()
	student_ans: string;
}
