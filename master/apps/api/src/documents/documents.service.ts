import { Injectable } from '@nestjs/common';
import { ExternalApiService } from 'src/integrations/external-api.service';
import { MockAiService } from 'src/mocks/mock-ai.service';
import { MockCloudService } from 'src/mocks/mock-cloud.service';

@Injectable()
export class DocumentsService {
	constructor(
		private readonly mockCloudService: MockCloudService,
		private readonly mockAiService: MockAiService,
		private readonly externalApiService: ExternalApiService,
	) { }

	async listDocuments() {
		// REAL API
		const externalDocuments = await this.externalApiService.listDocuments();
		if (externalDocuments) {
			return externalDocuments;
		}

		if (!this.externalApiService.isMockEnabled()) {
			throw new Error('External documents API returned no data while USE_MOCK_SERVICES=false');
		}

		// MOCKTEST fallback.
		return this.mockCloudService.listDocuments();
	}

	async getDocumentDetail(id: string) {
		// REAL API
		const externalExam = await this.externalApiService.getExamByDocumentId(id);
		if (externalExam) {
			return externalExam;
		}

		if (!this.externalApiService.isMockEnabled()) {
			throw new Error('External exam detail API returned no data while USE_MOCK_SERVICES=false');
		}

		// MOCKTEST
		this.mockCloudService.getDocumentById(id);
		// MOCKTEST
		return this.mockAiService.getExamByDocumentId(id);
	}
}
