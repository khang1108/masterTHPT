import { Module } from '@nestjs/common';
import { PracticeController } from './practice.controller';
import { PracticeService } from './practice.service';

@Module({
	controllers: [PracticeController],
	providers: [PracticeService],
})
export class PracticeModule { }
