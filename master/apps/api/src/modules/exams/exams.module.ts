import { Module } from '@nestjs/common';
import { PrismaModule } from 'src/infrastructure/prisma/prisma.module';
import { ExamsController } from './exams.controller';
import { ExamsService } from './exams.service';

@Module({
	imports: [PrismaModule],
	controllers: [ExamsController],
	providers: [ExamsService],
})
export class ExamsModule { }
