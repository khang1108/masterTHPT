import { Injectable, Logger, ServiceUnavailableException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { PrismaService } from 'src/infrastructure/prisma/prisma.service';
import { requireStudentByIdentity } from 'src/modules/students/student-identity';
import { postToAiService } from 'src/shared/ai/ai-client';
import { AskHintDto } from './dto/ask-hint.dto';
import { ReviewMistakeDto } from './dto/review-mistake.dto';

type HintLevels = {
	hint_1: string;
	hint_2: string;
	hint_3: string;
};

function normalizeReviewFeedback(feedback: unknown) {
	if (typeof feedback === 'string') {
		const parsed = parseMaybeJson(feedback);
		if (parsed !== null) {
			const nested = normalizeReviewFeedback(parsed);
			return nested || feedback.trim();
		}
		return feedback.trim();
	}

	if (Array.isArray(feedback)) {
		for (const item of feedback) {
			const value = normalizeReviewFeedback(item);
			if (value) {
				return value;
			}
		}
		return '';
	}

	if (feedback && typeof feedback === 'object') {
		const payload = feedback as {
			feedback?: unknown;
			reasoning?: unknown;
			content?: unknown;
			text?: unknown;
			results?: Array<{
				feedback?: unknown;
				reasoning?: unknown;
				content?: unknown;
				text?: unknown;
			}>;
		};

		for (const value of [payload.feedback, payload.content, payload.text, payload.reasoning]) {
			if (typeof value === 'string' && value.trim()) {
				return value.trim();
			}
		}

		if (Array.isArray(payload.results)) {
			for (const item of payload.results) {
				const value = normalizeReviewFeedback(item);
				if (value) {
					return value;
				}
			}
		}
	}

	return '';
}

function emptyHintLevels(): HintLevels {
	return {
		hint_1: '',
		hint_2: '',
		hint_3: '',
	};
}

function parseMaybeJson(text: string): unknown {
	const trimmed = text.trim();
	if (!trimmed || (!trimmed.startsWith('{') && !trimmed.startsWith('['))) {
		return null;
	}

	try {
		return JSON.parse(trimmed);
	} catch {
		return null;
	}
}

function extractHintFeedbackText(rawFeedback: unknown): string {
	if (typeof rawFeedback === 'string') {
		const parsed = parseMaybeJson(rawFeedback);
		if (parsed !== null) {
			const nested = extractHintFeedbackText(parsed);
			return nested || rawFeedback.trim();
		}
		return rawFeedback.trim();
	}

	if (Array.isArray(rawFeedback)) {
		for (const item of rawFeedback) {
			const value = extractHintFeedbackText(item);
			if (value) {
				return value;
			}
		}
		return '';
	}

	if (rawFeedback && typeof rawFeedback === 'object') {
		const payload = rawFeedback as {
			feedback?: unknown;
			reasoning?: unknown;
			results?: Array<{ feedback?: unknown; reasoning?: unknown }>;
		};

		if (typeof payload.feedback === 'string' && payload.feedback.trim()) {
			return payload.feedback.trim();
		}

		if (Array.isArray(payload.results)) {
			for (const item of payload.results) {
				if (typeof item?.feedback === 'string' && item.feedback.trim()) {
					return item.feedback.trim();
				}
			}
			for (const item of payload.results) {
				if (typeof item?.reasoning === 'string' && item.reasoning.trim()) {
					return item.reasoning.trim();
				}
			}
		}

		if (typeof payload.reasoning === 'string' && payload.reasoning.trim()) {
			return payload.reasoning.trim();
		}
	}

	return '';
}

function parseHintLevels(feedback: string): HintLevels {
	const levels = emptyHintLevels();
	const normalized = feedback
		.replace(/\r\n/g, '\n')
		.replace(/\\r\\n/g, '\n')
		.replace(/\\n/g, '\n')
		.trim();
	if (!normalized) {
		return levels;
	}

	const groupedRegex = /(hint|gợi\s*ý)\s*([1-3])\s*[:\-–\.)]?\s*([\s\S]*?)(?=(hint|gợi\s*ý)\s*[1-3]\s*[:\-–\.)]?|$)/gi;
	let groupedMatch: RegExpExecArray | null = groupedRegex.exec(normalized);
	while (groupedMatch !== null) {
		const level = `hint_${groupedMatch[2]}` as keyof HintLevels;
		const content = (groupedMatch[3] || '').trim();
		if (content && !levels[level]) {
			levels[level] = content;
		}
		groupedMatch = groupedRegex.exec(normalized);
	}

	if (levels.hint_1 || levels.hint_2 || levels.hint_3) {
		return levels;
	}

	// Fallback: some AI responses still collapse all hints into one paragraph
	// without explicit "Hint 1/2/3" labels. We split conservatively on sentence
	// boundaries so the UI can still reveal hints progressively instead of
	// showing the whole guidance as a single block.
	const sentenceParts = normalized
		.split(/(?<=[\.\!\?;:])\s+/)
		.map((part) => part.trim())
		.filter((part) => part.length > 0);

	if (sentenceParts.length >= 3) {
		levels.hint_1 = sentenceParts[0];
		levels.hint_2 = sentenceParts[1];
		levels.hint_3 = sentenceParts.slice(2).join(' ');
		return levels;
	}

	const lines = normalized
		.split(/\n+/)
		.map((line) => line.trim())
		.filter((line) => line.length > 0);

	if (lines.length === 0) {
		return levels;
	}

	if (lines.length === 1) {
		levels.hint_1 = lines[0];
		return levels;
	}

	if (lines.length === 2) {
		levels.hint_1 = lines[0];
		levels.hint_2 = lines[1];
		return levels;
	}

	levels.hint_1 = lines[0];
	levels.hint_2 = lines[1];
	levels.hint_3 = lines.slice(2).join(' ');
	return levels;
}

function flattenHintLevels(levels: HintLevels): string {
	const lines: string[] = [];
	if (levels.hint_1) {
		lines.push(`Hint 1: ${levels.hint_1}`);
	}
	if (levels.hint_2) {
		lines.push(`Hint 2: ${levels.hint_2}`);
	}
	if (levels.hint_3) {
		lines.push(`Hint 3: ${levels.hint_3}`);
	}
	return lines.join('\n');
}

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
			throw new ServiceUnavailableException('Không thể lấy gợi ý lúc này - 1');
		}

		try {
			const data = await postToAiService<{
				user_id?: string;
				exam_id?: string;
				question_id?: string;
				feedback?: unknown;
			}>(
				this.configService,
				{
					intent: 'ASK_HINT',
					user_id: canonicalUserId,
					exam_id: dto.exam_id,
					question_id: dto.question_id,
				},
			);
			const feedback = extractHintFeedbackText(data?.feedback);
			const hints = parseHintLevels(feedback);

			return {
				user_id: data?.user_id ?? canonicalUserId,
				exam_id: data?.exam_id ?? dto.exam_id,
				question_id: data?.question_id ?? dto.question_id,
				feedback: flattenHintLevels(hints) || feedback,
				hints,
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
				feedback?: unknown;
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
				feedback: normalizeReviewFeedback(data?.feedback),
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
