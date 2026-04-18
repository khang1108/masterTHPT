import { Module } from '@nestjs/common';
import { PrismaModule } from 'src/infrastructure/prisma/prisma.module';
import { HistoryController } from './history.controller';
import { HistoryService } from './history.service';

@Module({
	imports: [PrismaModule],
	controllers: [HistoryController],
	providers: [HistoryService],
	exports: [HistoryService],
})
export class HistoryModule { }
