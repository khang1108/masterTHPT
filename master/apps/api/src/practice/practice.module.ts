import { Module } from '@nestjs/common';
import { IntegrationsModule } from 'src/integrations/integrations.module';
import { MocksModule } from 'src/mocks/mocks.module';
import { PrismaModule } from 'src/prisma/prisma.module';
import { PracticeController } from './practice.controller';
import { PracticeService } from './practice.service';

@Module({
	imports: [MocksModule, PrismaModule, IntegrationsModule],
	controllers: [PracticeController],
	providers: [PracticeService],
})
export class PracticeModule { }
