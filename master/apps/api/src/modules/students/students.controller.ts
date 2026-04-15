import { Body, Controller, Get, Patch, UseGuards } from '@nestjs/common';
import { JwtPayload } from 'src/shared/auth/jwt-payload.type';
import { CurrentUser } from 'src/shared/decorators/current-user.decorator';
import { JwtAuthGuard } from 'src/shared/guards/jwt-auth.guard';
import { UpdateStudentProfileDto } from './dto/update-student-profile.dto';
import { StudentsService } from './students.service';

@Controller('students')
@UseGuards(JwtAuthGuard)
export class StudentsController {
	constructor(private readonly studentsService: StudentsService) { }

	@Get('me')
	getMe(@CurrentUser() user: JwtPayload) {
		return this.studentsService.getMe(user.sub);
	}

	@Patch('me')
	updateMe(@CurrentUser() user: JwtPayload, @Body() dto: UpdateStudentProfileDto) {
		return this.studentsService.updateMe(user.sub, dto);
	}
}
