import { Injectable, NotFoundException } from '@nestjs/common';
import { ASCII_SECTION_NAME_BY_TYPE, buildExamSections, ExamMetadataShape, sortItemsByReferenceOrder } from 'src/common/exams/exam-content';
import { PrismaService } from 'src/prisma/prisma.service';

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

	async listDocuments() {
		const exams = await this.prisma.exam.findMany({
			where: {
				generated: false,
			},
			select: {
				id: true,
				subject: true,
				grade: true,
				exam_type: true,
				year: true,
				source: true,
				total_questions: true,
				duration: true,
				metadata: true,
				created_at: true,
			},
		});

		return exams.sort(
			(a, b) => this.toEpoch(b.created_at) - this.toEpoch(a.created_at),
		);
	}

	async getDocumentDetail(id: string) {
		const exam = await this.prisma.exam.findUnique({
			where: { id },
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
			throw new NotFoundException('Khong tim thay de thi');
		}

		const questionIds = exam.questions ?? [];
		const questions = questionIds.length === 0
			? []
			: await this.prisma.question.findMany({
				where: {
					id: {
						in: questionIds,
					},
				},
			});
		const sortedQuestions = sortItemsByReferenceOrder(questionIds, questions);

		const metadata = (exam.metadata ?? {}) as ExamMetadataShape;
		const sections = buildExamSections(sortedQuestions, ASCII_SECTION_NAME_BY_TYPE);

		return {
			exam_id: exam.id,
			source_type: metadata.source_type ?? 'documents_library',
			subject: exam.subject,
			grade: exam.grade,
			exam_type: exam.exam_type,
			total_questions: sortedQuestions.length > 0 ? sortedQuestions.length : exam.total_questions,
			duration_minutes: metadata.duration_minutes ?? exam.duration,
			sections,
		};
	}
}
