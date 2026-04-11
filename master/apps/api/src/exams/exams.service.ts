import { Injectable } from '@nestjs/common';
import { ExternalApiService } from 'src/integrations/external-api.service';
import { MockAiService } from 'src/mocks/mock-ai.service';
import { PrismaService } from 'src/prisma/prisma.service';
import { SubmitExamDto } from './dto/submit-exam.dto';

@Injectable()
export class ExamsService {
	constructor(
		private readonly mockAiService: MockAiService,
		private readonly prisma: PrismaService,
		private readonly externalApiService: ExternalApiService,
	) { }

	async submit(dto: SubmitExamDto) {
		const aiPayload = {
			exam_id: dto.full_exam.exam_id,
			source: dto.full_exam.source ?? 'unknown',
			subject: dto.full_exam.subject,
			exam_type: dto.full_exam.exam_type,
			total_questions: dto.full_exam.total_questions,
			sections: dto.full_exam.sections,
			uuid: dto.student_id,
		};

		// REAL API
		const externalEvaluation = await this.externalApiService.evaluateExam({
			...aiPayload,
		});
		const evaluation =
			externalEvaluation ??
			(this.externalApiService.isMockEnabled() ? this.mockAiService.evaluate(dto) : null);

		if (!evaluation) {
			throw new Error('External evaluate API returned no data while USE_MOCK_SERVICES=false');
		}

		await this.prisma.student.updateMany({
			where: {
				id: dto.student_id,
				is_first_login: true,
			},
			data: {
				is_first_login: false,
			},
		});

		return evaluation;
	}
}
