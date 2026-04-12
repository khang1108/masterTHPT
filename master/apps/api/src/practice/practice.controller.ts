import {
	Body,
	Controller,
	Post,
	UploadedFile,
	UseGuards,
	UseInterceptors,
} from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import { JwtPayload } from 'src/auth/types';
import { CurrentUser } from 'src/common/decorators/current-user.decorator';
import { JwtAuthGuard } from 'src/common/guards/jwt-auth.guard';
import { GenerateOnboardingExamDto } from './dto/generate-onboarding-exam.dto';
import { GeneratePracticeDto } from './dto/generate-practice.dto';
import { PracticeService } from './practice.service';

@Controller('practice')
@UseGuards(JwtAuthGuard)
export class PracticeController {
	constructor(private readonly practiceService: PracticeService) { }

	@Post('generate')
	@UseInterceptors(FileInterceptor('file'))
	// MOCKTEST
	generate(
		@CurrentUser() user: JwtPayload,
		@Body() dto: GeneratePracticeDto,
		@UploadedFile() file?: Express.Multer.File,
	) {
		return this.practiceService.generateExam(user.sub, dto, file);
	}

	@Post('onboarding')
	// MOCKTEST
	generateOnboardingExam(
		@CurrentUser() user: JwtPayload,
		@Body() dto: GenerateOnboardingExamDto,
	) {
		return this.practiceService.generateOnboardingExam(user.sub, dto);
	}
}
