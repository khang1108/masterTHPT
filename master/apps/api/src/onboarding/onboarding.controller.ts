import {
	Body,
	Controller,
	Post,
	UseGuards,
} from '@nestjs/common';
import { JwtPayload } from 'src/auth/types';
import { CurrentUser } from 'src/common/decorators/current-user.decorator';
import { JwtAuthGuard } from 'src/common/guards/jwt-auth.guard';
import { GenerateOnboardingExamDto } from './dto/generate-onboarding-exam.dto';
import { OnboardingService } from './onboarding.service';

@Controller('onboarding')
@UseGuards(JwtAuthGuard)
export class OnboardingController {
	constructor(private readonly onboardingService: OnboardingService) { }

	@Post('exam')
	generateOnboardingExam(
		@CurrentUser() user: JwtPayload,
		@Body() dto: GenerateOnboardingExamDto,
	) {
		return this.onboardingService.generateOnboardingExam(user.sub, dto);
	}
}
