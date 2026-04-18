import { Controller, Get, Param, UseGuards } from '@nestjs/common';
import { CurrentUser } from 'src/shared/decorators/current-user.decorator';
import { JwtPayload } from 'src/shared/auth/jwt-payload.type';
import { JwtAuthGuard } from 'src/shared/guards/jwt-auth.guard';
import { DocumentsService } from './documents.service';

@Controller('documents')
@UseGuards(JwtAuthGuard)
export class DocumentsController {
	constructor(private readonly documentsService: DocumentsService) { }

	@Get()
	// MOCKTEST
	getDocuments(@CurrentUser() user: JwtPayload) {
		return this.documentsService.listDocuments(user.sub);
	}

	@Get(':id')
	// MOCKTEST
	getDocumentDetail(@Param('id') id: string) {
		return this.documentsService.getDocumentDetail(id);
	}
}
