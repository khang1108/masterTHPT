import { Module } from '@nestjs/common';
import { IntegrationsModule } from 'src/integrations/integrations.module';
import { MocksModule } from 'src/mocks/mocks.module';
import { DocumentsController } from './documents.controller';
import { DocumentsService } from './documents.service';

@Module({
	imports: [MocksModule, IntegrationsModule],
	controllers: [DocumentsController],
	providers: [DocumentsService],
})
export class DocumentsModule { }
