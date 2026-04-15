import { Body, Controller, Post, UseGuards } from '@nestjs/common';
import { JwtPayload } from 'src/shared/auth/jwt-payload.type';
import { CurrentUser } from 'src/shared/decorators/current-user.decorator';
import { JwtAuthGuard } from 'src/shared/guards/jwt-auth.guard';
import { SubmitExamDto } from './dto/submit-exam.dto';
import { ExamsService } from './exams.service';

@Controller('exams')
@UseGuards(JwtAuthGuard)
export class ExamsController {
	constructor(private readonly examsService: ExamsService) { }

	@Post('submit')
	submit(@CurrentUser() user: JwtPayload, @Body() dto: SubmitExamDto) {
		return this.examsService.submit({
			...dto,
			student_id: dto.student_id ?? user.sub,
		});
	}
}
