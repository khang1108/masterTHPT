import { Module } from '@nestjs/common';
import { HistoryModule } from 'src/modules/history/history.module';
import { PrismaModule } from 'src/infrastructure/prisma/prisma.module';
import { ExamsController } from './exams.controller';
import { ExamsService } from './exams.service';

@Module({
	imports: [PrismaModule, HistoryModule],
	controllers: [ExamsController],
	providers: [ExamsService],
})
export class ExamsModule { }
