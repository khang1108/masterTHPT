import { Body, Controller, Post, UseGuards } from '@nestjs/common';
import { JwtPayload } from 'src/auth/types';
import { CurrentUser } from 'src/common/decorators/current-user.decorator';
import { JwtAuthGuard } from 'src/common/guards/jwt-auth.guard';
import { AskHintDto } from './dto/ask-hint.dto';
import { ReviewMistakeDto } from './dto/review-mistake.dto';
import { HintsService } from './hints.service';

@Controller('hints')
@UseGuards(JwtAuthGuard)
export class HintsController {
	constructor(private readonly hintsService: HintsService) { }

	@Post()
	askHint(@CurrentUser() user: JwtPayload, @Body() dto: AskHintDto) {
		return this.hintsService.askHint(user.sub, dto);
	}

	@Post('review-mistake')
	reviewMistake(@CurrentUser() user: JwtPayload, @Body() dto: ReviewMistakeDto) {
		return this.hintsService.reviewMistake(user.sub, dto);
	}
}
