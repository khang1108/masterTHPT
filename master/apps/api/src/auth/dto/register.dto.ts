import { IsEmail, IsInt, IsNotEmpty, IsString, Max, Min, MinLength } from 'class-validator';

export class RegisterDto {
	@IsString()
	@IsNotEmpty()
	name: string;

	@IsEmail()
	email: string;

	@IsString()
	@MinLength(6)
	password: string;

	@IsInt()
	@Min(10)
	@Max(12)
	grade: number;
}
