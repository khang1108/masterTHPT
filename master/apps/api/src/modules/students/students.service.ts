import { NotFoundException } from '@nestjs/common';
import { Injectable } from '@nestjs/common';
import { PrismaService } from 'src/infrastructure/prisma/prisma.service';
import { UpdateStudentProfileDto } from './dto/update-student-profile.dto';
import { hasCompletedProfile } from './student-profile-state';
import { StudentResponse, toStudentResponse } from './student-response';

@Injectable()
export class StudentsService {
	constructor(private readonly prisma: PrismaService) { }

	async getMe(studentId: string): Promise<StudentResponse> {
		const student = await this.prisma.student.findUnique({
			where: { id: studentId },
		});

		if (!student) {
			throw new NotFoundException('Không tìm thấy tài khoản học sinh');
		}

		return toStudentResponse(student);
	}

	async updateMe(studentId: string, dto: UpdateStudentProfileDto): Promise<StudentResponse> {
		const profile = {
			name: dto.name.trim(),
			grade: dto.grade,
			school: dto.school.trim(),
			learning_goal: dto.learning_goal.trim(),
		};
		const student = await this.prisma.student.update({
			where: { id: studentId },
			data: {
				...profile,
				profile_completed: hasCompletedProfile(profile),
			},
		});

		return toStudentResponse(student);
	}
}
