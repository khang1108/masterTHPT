import { IsNotEmpty, IsString } from 'class-validator';

export class AskHintDto {
	@IsString()
	@IsNotEmpty()
	exam_id: string;

	@IsString()
	@IsNotEmpty()
	question_id: string;
}
