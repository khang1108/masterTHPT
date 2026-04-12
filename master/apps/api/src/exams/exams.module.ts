import { Module } from '@nestjs/common';
import { IntegrationsModule } from 'src/integrations/integrations.module';
import { MocksModule } from 'src/mocks/mocks.module';
import { PrismaModule } from 'src/prisma/prisma.module';
import { ExamsController } from './exams.controller';
import { ExamsService } from './exams.service';

@Module({
	imports: [MocksModule, PrismaModule, IntegrationsModule],
	controllers: [ExamsController],
	providers: [ExamsService],
})
export class ExamsModule { }
