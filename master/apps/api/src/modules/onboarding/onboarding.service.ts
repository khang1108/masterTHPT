import { BadRequestException, Injectable, NotFoundException } from '@nestjs/common';
import { ACCENTED_SECTION_NAME_BY_TYPE, buildExamSections, ExamMetadataShape, sortItemsByReferenceOrder } from 'src/shared/exams/exam-content';
import { PrismaService } from 'src/infrastructure/prisma/prisma.service';
import { findQuestionDocumentsByAnyIds } from 'src/shared/mongo/read-models';
import { hasCompletedProfile } from 'src/modules/students/student-profile-state';
import { GenerateOnboardingExamDto } from './dto/generate-onboarding-exam.dto';

@Injectable()
export class OnboardingService {
	constructor(
		private readonly prisma: PrismaService,
	) { }

	async generateOnboardingExam(studentId: string, dto: GenerateOnboardingExamDto) {
		const student = await this.prisma.student.findUnique({
			where: { id: studentId },
		});

		if (!student) {
			throw new BadRequestException('Không tìm thấy tài khoản học sinh');
		}

		if (!(Boolean(student.profile_completed) || hasCompletedProfile(student))) {
			throw new BadRequestException('Vui lòng điền thông tin cá nhân trước');
		}

		const isFirstLogin =
			'is_first_login' in student &&
			typeof student.is_first_login === 'boolean' &&
			student.is_first_login;

		if (!isFirstLogin) {
			throw new BadRequestException('Bạn đã hoàn thành bài thi đầu vào trước đó');
		}

		const subject = dto.subject.trim();
		const examType = dto.exam_type.trim();

		const exam = await this.prisma.exam.findFirst({
			where: {
				subject,
				grade: dto.grade,
				exam_type: examType,
				generated: false,
			},
			orderBy: [
				{ year: 'desc' },
				{ created_at: 'desc' },
			],
			select: {
				id: true,
				subject: true,
				grade: true,
				exam_type: true,
				questions: true,
				total_questions: true,
				duration: true,
				metadata: true,
			},
		});

		if (!exam) {
			throw new NotFoundException(
				`Không tìm thấy đề phù hợp cho môn ${subject}, ${examType}, lớp ${dto.grade}`,
			);
		}

		const questionIds = exam.questions ?? [];
		const questions = questionIds.length === 0
			? []
			: await findQuestionDocumentsByAnyIds(this.prisma, questionIds);
		const sortedQuestions = sortItemsByReferenceOrder(questionIds, questions);

		const metadata = (exam.metadata ?? {}) as ExamMetadataShape;
		const sections = buildExamSections(sortedQuestions, ACCENTED_SECTION_NAME_BY_TYPE);

		return {
			exam_id: exam.id,
			source_type: metadata.source_type ?? 'onboarding_existing_exam',
			subject: exam.subject,
			exam_type: exam.exam_type,
			total_questions: sortedQuestions.length > 0 ? sortedQuestions.length : exam.total_questions,
			duration_minutes: metadata.duration_minutes ?? exam.duration,
			sections,
		};
	}
}
