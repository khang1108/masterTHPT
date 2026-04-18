import { ForbiddenException, Injectable, Logger, NotFoundException, ServiceUnavailableException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { postToAiService } from 'src/shared/ai/ai-client';
import { isAnswerCorrect } from 'src/shared/exams/evaluation';
import { sortItemsByReferenceOrder } from 'src/shared/exams/exam-content';
import { PrismaService } from 'src/infrastructure/prisma/prisma.service';
import { requireStudentByIdentity } from 'src/modules/students/student-identity';
import {
	findExamDocumentByAnyId,
	findExamDocumentsByAnyIds,
	findQuestionDocumentByAnyId,
} from 'src/shared/mongo/read-models';
import { CheckPracticeQuestionDto } from './dto/check-practice-question.dto';
import { UpdatePracticeDto } from './dto/update-practice.dto';

@Injectable()
export class PracticeService {
	private readonly logger = new Logger(PracticeService.name);

	constructor(
		private readonly prisma: PrismaService,
		private readonly configService: ConfigService,
	) { }

	async listUserPracticeExams(userId: string) {
		const student = await requireStudentByIdentity(this.prisma, userId);
		const examIds = await this.getUserPracticeExamIds(student.user_id);
		if (examIds.length === 0) {
			return [];
		}

		const exams = await findExamDocumentsByAnyIds(this.prisma, examIds);

		return sortItemsByReferenceOrder(examIds, exams).map((exam) => ({
			id: exam.id,
			subject: exam.subject,
			source: exam.source ?? 'Nguồn chưa cập nhật',
			total_questions: exam.total_questions ?? 0,
			exam_type: exam.exam_type,
			grade: exam.grade ?? 0,
			year: exam.year ?? 0,
		}));
	}

	async checkQuestion(userId: string, dto: CheckPracticeQuestionDto) {
		const student = await requireStudentByIdentity(this.prisma, userId);
		const canonicalUserId = student.user_id;
		// Practice checking only works for exams explicitly assigned to the student.
		// Keep this authorization check close to the entry point so future mutations reuse it.
		const examIds = await this.getUserPracticeExamIds(canonicalUserId);
		if (!examIds.includes(dto.exam_id)) {
			throw new ForbiddenException('Bạn không có quyền luyện đề này');
		}

		const exam = await findExamDocumentByAnyId(this.prisma, dto.exam_id);

		if (!exam) {
			throw new NotFoundException('Không tìm thấy đề luyện tập');
		}

		if (!(exam.questions ?? []).includes(dto.question_id)) {
			throw new NotFoundException('Câu hỏi không thuộc đề này');
		}

		const question = await findQuestionDocumentByAnyId(this.prisma, dto.question_id);

		if (!question) {
			throw new NotFoundException('Không tìm thấy câu hỏi');
		}

		const correctAnswer = question.correct_answer ?? '';
		const studentAnswer = (dto.student_answer ?? '').trim();

		return {
			question_id: dto.question_id,
			student_answer: studentAnswer,
			correct_answer: correctAnswer,
			is_correct: isAnswerCorrect(studentAnswer, correctAnswer),
		};
	}

	async updatePractice(userId: string, dto: UpdatePracticeDto) {
		const student = await requireStudentByIdentity(this.prisma, userId);
		const canonicalUserId = student.user_id;
		// The AI service is responsible for updating the practice assignment out of band.
		// This endpoint only triggers that workflow and lets the frontend refresh afterwards.
		if (!this.configService.get<string>('AI_API_BASE_URL')?.trim()) {
			this.logger.warn('AI_API_BASE_URL is not configured for practice updates');
			throw new ServiceUnavailableException('Không thể cập nhật danh sách luyện tập lúc này');
		}

		try {
			await postToAiService(
				this.configService,
				{
					intent: 'UPDATE_PRACTICE',
					user_id: canonicalUserId,
					user_message: dto.request,
				},
			);

			return {
				success: true,
			};
		} catch (error) {
			this.logger.warn(`Failed to update practice for user ${userId}: ${error instanceof Error ? error.message : 'Unknown error'}`);
			throw new ServiceUnavailableException('Không thể cập nhật danh sách luyện tập lúc này');
		}
	}

	private async getUserPracticeExamIds(userId: string) {
		// Shared helper to keep the student-to-practice lookup logic in one place.
		const practice = await this.prisma.practice.findUnique({
			where: { user_id: userId },
			select: {
				exam_ids: true,
			},
		});

		return practice?.exam_ids ?? [];
	}
}
