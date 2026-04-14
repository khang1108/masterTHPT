import { ForbiddenException, Injectable, Logger, NotFoundException, ServiceUnavailableException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { postToAiService } from 'src/common/ai/ai-client';
import { isAnswerCorrect } from 'src/common/exams/evaluation';
import { sortItemsByReferenceOrder } from 'src/common/exams/exam-content';
import { PrismaService } from 'src/prisma/prisma.service';
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
		const examIds = await this.getUserPracticeExamIds(userId);
		if (examIds.length === 0) {
			return [];
		}

		const exams = await this.prisma.exam.findMany({
			where: {
				id: {
					in: examIds,
				},
			},
			select: {
				id: true,
				subject: true,
				source: true,
				total_questions: true,
				exam_type: true,
				grade: true,
				year: true,
			},
		});

		return sortItemsByReferenceOrder(examIds, exams);
	}

	async checkQuestion(userId: string, dto: CheckPracticeQuestionDto) {
		// Practice checking only works for exams explicitly assigned to the student.
		// Keep this authorization check close to the entry point so future mutations reuse it.
		const examIds = await this.getUserPracticeExamIds(userId);
		if (!examIds.includes(dto.exam_id)) {
			throw new ForbiddenException('Bạn không có quyền luyện đề này');
		}

		const exam = await this.prisma.exam.findUnique({
			where: { id: dto.exam_id },
			select: {
				questions: true,
			},
		});

		if (!exam) {
			throw new NotFoundException('Không tìm thấy đề luyện tập');
		}

		if (!(exam.questions ?? []).includes(dto.question_id)) {
			throw new NotFoundException('Câu hỏi không thuộc đề này');
		}

		const question = await this.prisma.question.findUnique({
			where: { id: dto.question_id },
			select: {
				correct_answer: true,
			},
		});

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
		// The AI service is responsible for updating the practice assignment out of band.
		// This endpoint only triggers that workflow and lets the frontend refresh afterwards.
		if (!this.configService.get<string>('AI_API_BASE_URL')?.trim()) {
			throw new ServiceUnavailableException('AI service chưa được cấu hình');
		}

		try {
			await postToAiService(
				this.configService,
				{
					intent: 'UPDATE_PRACTICE',
					user_id: userId,
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
