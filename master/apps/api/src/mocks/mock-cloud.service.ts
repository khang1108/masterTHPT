import { Injectable, NotFoundException } from '@nestjs/common';
import { MOCK_DOCUMENTS } from './data/mock-documents';

@Injectable()
export class MockCloudService {
	listDocuments() {
		return MOCK_DOCUMENTS;
	}

	getDocumentById(id: string) {
		const item = MOCK_DOCUMENTS.find((doc) => doc.id === id);
		if (!item) {
			throw new NotFoundException('Khong tim thay de thi');
		}

		return item;
	}
}
