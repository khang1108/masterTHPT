import { Body, Controller, Post, UseGuards } from '@nestjs/common';
import { JwtPayload } from 'src/auth/types';
import { CurrentUser } from 'src/common/decorators/current-user.decorator';
import { JwtAuthGuard } from 'src/common/guards/jwt-auth.guard';
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
