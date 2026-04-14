import { Body, Controller, Get, Post, UseGuards } from '@nestjs/common';
import { JwtPayload } from 'src/auth/types';
import { CurrentUser } from 'src/common/decorators/current-user.decorator';
import { JwtAuthGuard } from 'src/common/guards/jwt-auth.guard';
import { CheckPracticeQuestionDto } from './dto/check-practice-question.dto';
import { UpdatePracticeDto } from './dto/update-practice.dto';
import { PracticeService } from './practice.service';

@Controller('practice')
@UseGuards(JwtAuthGuard)
export class PracticeController {
	constructor(private readonly practiceService: PracticeService) { }

	@Get()
	listUserPracticeExams(@CurrentUser() user: JwtPayload) {
		return this.practiceService.listUserPracticeExams(user.sub);
	}

	@Post('check-question')
	checkQuestion(
		@CurrentUser() user: JwtPayload,
		@Body() dto: CheckPracticeQuestionDto,
	) {
		return this.practiceService.checkQuestion(user.sub, dto);
	}

	@Post('update')
	updatePractice(
		@CurrentUser() user: JwtPayload,
		@Body() dto: UpdatePracticeDto,
	) {
		return this.practiceService.updatePractice(user.sub, dto);
	}
}
