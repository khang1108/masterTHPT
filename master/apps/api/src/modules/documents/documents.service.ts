import { Injectable, NotFoundException } from '@nestjs/common';
import { ASCII_SECTION_NAME_BY_TYPE, buildExamSections, sortItemsByReferenceOrder } from 'src/shared/exams/exam-content';
import { PrismaService } from 'src/infrastructure/prisma/prisma.service';
import {
	findExamDocumentByAnyId,
	findPublishedExamDocuments,
	findHistoryDocumentsByUserId,
	findQuestionDocumentsByAnyIds,
} from 'src/shared/mongo/read-models';
import { requireStudentByIdentity } from 'src/modules/students/student-identity';

@Injectable()
export class DocumentsService {
	constructor(private readonly prisma: PrismaService) { }

	private toEpoch(value?: string | null): number {
		if (!value) {
			return 0;
		}

		const normalized = value.replace(/^"|"$/g, '');
		const parsed = Date.parse(normalized);
		return Number.isNaN(parsed) ? 0 : parsed;
	}

	private async getCompletionExamIdSet(userId: string) {
		const student = await requireStudentByIdentity(this.prisma, userId);
		const histories = await findHistoryDocumentsByUserId(this.prisma, student.user_id);

		return new Set(
			histories
				.map((history) => history.exam_id.trim())
				.filter((examId) => examId.length > 0),
		);
	}

	async listDocuments(userId: string) {
		const exams = await findPublishedExamDocuments(this.prisma);
		const completedExamIds = await this.getCompletionExamIdSet(userId);

		return exams.sort(
			(a, b) => this.toEpoch(b.created_at) - this.toEpoch(a.created_at),
		).map((exam) => ({
			id: exam.id,
			subject: exam.subject || 'Đề chưa xác định',
			grade: exam.grade ?? 0,
			exam_type: exam.exam_type || 'Đề chưa xác định',
			year: exam.year ?? 0,
			source: exam.source ?? 'Nguồn chưa cập nhật',
			total_questions: exam.total_questions ?? 0,
			duration: exam.duration ?? 0,
			is_completed: completedExamIds.has(exam.id) || completedExamIds.has(exam.mongo_id),
			created_at: exam.created_at ?? undefined,
		}));
	}

	private async buildDocumentDetail(id: string) {
		const exam = await findExamDocumentByAnyId(this.prisma, id);

		if (!exam) {
			throw new NotFoundException('Khong tim thay de thi');
		}

		const questionIds = exam.questions ?? [];
		const questions = await findQuestionDocumentsByAnyIds(this.prisma, questionIds);
		const sortedQuestions = sortItemsByReferenceOrder(questionIds, questions);

		const sections = buildExamSections(sortedQuestions, ASCII_SECTION_NAME_BY_TYPE);

		return {
			exam_id: exam.id,
			source_type: 'documents_library',
			subject: exam.subject || 'Đề chưa xác định',
			grade: exam.grade ?? undefined,
			exam_type: exam.exam_type || 'Đề chưa xác định',
			total_questions: sortedQuestions.length > 0 ? sortedQuestions.length : (exam.total_questions ?? 0),
			duration_minutes: exam.duration ?? 0,
			sections,
		};
	}

	async getDocumentDetail(id: string) {
		return this.buildDocumentDetail(id);
	}
}
