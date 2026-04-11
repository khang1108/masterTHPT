import { BadRequestException, Injectable } from '@nestjs/common';
import { ExternalApiService } from 'src/integrations/external-api.service';
import { MockAiService } from 'src/mocks/mock-ai.service';
import { PrismaService } from 'src/prisma/prisma.service';
import { GenerateOnboardingExamDto } from './dto/generate-onboarding-exam.dto';
import { GeneratePracticeDto } from './dto/generate-practice.dto';

@Injectable()
export class PracticeService {
	constructor(
		private readonly mockAiService: MockAiService,
		private readonly prisma: PrismaService,
		private readonly externalApiService: ExternalApiService,
	) { }

	async generateExam(studentId: string, dto: GeneratePracticeDto, file?: Express.Multer.File) {
		const sourceType = file ? 'upload_file' : dto.embedded_text ? 'text_input' : 'manual';
		const payload = {
			uuid: studentId,
			sourceType,
			subject: dto.subject,
			examType: dto.exam_type,
			embeddedText: dto.embedded_text,
		};

		// REAL API
		const externalExam = await this.externalApiService.generateExam(payload);
		if (externalExam) {
			return externalExam;
		}

		if (!this.externalApiService.isMockEnabled()) {
			throw new BadRequestException(
				'External generate exam API returned no data while USE_MOCK_SERVICES=false',
			);
		}

		// MOCKTEST
		return this.mockAiService.generateExam(payload);
	}

	async generateOnboardingExam(studentId: string, dto: GenerateOnboardingExamDto) {
		const student = await this.prisma.student.findUnique({
			where: { id: studentId },
		});

		if (!student) {
			throw new BadRequestException('Không tìm thấy tài khoản học sinh');
		}

		const isFirstLogin =
			'is_first_login' in student &&
			typeof student.is_first_login === 'boolean' &&
			student.is_first_login;

		if (!isFirstLogin) {
			throw new BadRequestException('Bạn đã hoàn thành bài thi đầu vào trước đó');
		}

		const firstSubject = dto.subjects[0]?.subject?.trim();
		if (!firstSubject) {
			throw new BadRequestException('Vui lòng thêm ít nhất một môn học hợp lệ');
		}

		const normalizedSubjects = dto.subjects.map((subject) => ({
			subject: subject.subject.trim(),
			scores: subject.scores.map((score) => ({
				label: score.label.trim(),
				value: score.value.trim(),
			})),
		}));

		const payload = {
			uuid: studentId,
			sourceType: 'first_login_onboarding',
			subject: firstSubject,
			examType: 'onboarding_assessment',
			subjects: normalizedSubjects,
		};

		// REAL API
		const externalExam = await this.externalApiService.generateExam(payload);
		if (externalExam) {
			return externalExam;
		}

		if (!this.externalApiService.isMockEnabled()) {
			throw new BadRequestException(
				'External onboarding generate API returned no data while USE_MOCK_SERVICES=false',
			);
		}

		// MOCKTEST fallback.
		return this.mockAiService.generateExam(payload);
	}
}
