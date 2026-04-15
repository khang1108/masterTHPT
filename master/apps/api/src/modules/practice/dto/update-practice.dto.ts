import { IsNotEmpty, IsString } from 'class-validator';

export class UpdatePracticeDto {
	@IsString()
	@IsNotEmpty()
	request: string;
}
