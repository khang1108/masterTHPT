import { Controller, Get, Param, UseGuards } from '@nestjs/common';
import { JwtAuthGuard } from 'src/shared/guards/jwt-auth.guard';
import { DocumentsService } from './documents.service';

@Controller('documents')
@UseGuards(JwtAuthGuard)
export class DocumentsController {
	constructor(private readonly documentsService: DocumentsService) { }

	@Get()
	// MOCKTEST
	getDocuments() {
		return this.documentsService.listDocuments();
	}

	@Get(':id')
	// MOCKTEST
	getDocumentDetail(@Param('id') id: string) {
		return this.documentsService.getDocumentDetail(id);
	}
}
