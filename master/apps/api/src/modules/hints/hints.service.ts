import { Injectable, Logger, ServiceUnavailableException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { PrismaService } from 'src/infrastructure/prisma/prisma.service';
import { requireStudentByIdentity } from 'src/modules/students/student-identity';
import { postToAiService } from 'src/shared/ai/ai-client';
import { AskHintDto } from './dto/ask-hint.dto';
import { ReviewMistakeDto } from './dto/review-mistake.dto';

@Injectable()
export class HintsService {
	private readonly logger = new Logger(HintsService.name);

	constructor(
		private readonly configService: ConfigService,
		private readonly prisma: PrismaService,
	) { }

	async askHint(userId: string, dto: AskHintDto) {
		const student = await requireStudentByIdentity(this.prisma, userId);
		const canonicalUserId = student.user_id;
		// Hint generation is delegated to AI, while the API layer keeps the contract stable
		// for the frontend even if the upstream payload changes later.
		if (!this.configService.get<string>('AI_API_BASE_URL')?.trim()) {
			this.logger.warn('AI_API_BASE_URL is not configured for askHint');
			throw new ServiceUnavailableException('Không thể lấy gợi ý lúc này');
		}

		try {
			const data = await postToAiService<{
				user_id?: string;
				exam_id?: string;
				question_id?: string;
				feedback?: string;
			}>(
				this.configService,
				{
					intent: 'ASK_HINT',
					user_id: canonicalUserId,
					exam_id: dto.exam_id,
					question_id: dto.question_id,
				},
			);

			return {
				user_id: data?.user_id ?? canonicalUserId,
				exam_id: data?.exam_id ?? dto.exam_id,
				question_id: data?.question_id ?? dto.question_id,
				feedback: data?.feedback ?? '',
			};
		} catch (error) {
			this.logger.warn(`Failed to ask hint for exam ${dto.exam_id}, question ${dto.question_id}: ${error instanceof Error ? error.message : 'Unknown error'}`);
			throw new ServiceUnavailableException(
				error instanceof Error && error.message
					? error.message
					: 'Không thể lấy gợi ý lúc này',
			);
		}
	}

	async reviewMistake(userId: string, dto: ReviewMistakeDto) {
		const student = await requireStudentByIdentity(this.prisma, userId);
		const canonicalUserId = student.user_id;
		// Review-mistake uses a separate intent because it depends on the student's answer,
		// unlike generic hints which only need exam/question context.
		if (!this.configService.get<string>('AI_API_BASE_URL')?.trim()) {
			this.logger.warn('AI_API_BASE_URL is not configured for reviewMistake');
			throw new ServiceUnavailableException('Không thể lấy giải thích lúc này');
		}

		try {
			const data = await postToAiService<{
				user_id?: string;
				question_id?: string;
				feedback?: string;
			}>(
				this.configService,
				{
					intent: 'REVIEW_MISTAKE',
					user_id: canonicalUserId,
					question_id: dto.question_id,
					student_answers: {
						question_id: dto.question_id,
						student_answer: dto.student_ans,
					},
				},
			);

			return {
				user_id: data?.user_id ?? canonicalUserId,
				question_id: data?.question_id ?? dto.question_id,
				feedback: data?.feedback ?? '',
			};
		} catch (error) {
			this.logger.warn(`Failed to review mistake for question ${dto.question_id}: ${error instanceof Error ? error.message : 'Unknown error'}`);
			throw new ServiceUnavailableException(
				error instanceof Error && error.message
					? error.message
					: 'Không thể lấy giải thích lúc này',
			);
		}
	}
}
