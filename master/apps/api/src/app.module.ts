import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { AppController } from './app.controller';
import { AuthModule } from './modules/auth/auth.module';
import { DocumentsModule } from './modules/documents/documents.module';
import { ExamsModule } from './modules/exams/exams.module';
import { HintsModule } from './modules/hints/hints.module';
import { HistoryModule } from './modules/history/history.module';
import { OnboardingModule } from './modules/onboarding/onboarding.module';
import { PracticeModule } from './modules/practice/practice.module';
import { PrismaModule } from './infrastructure/prisma/prisma.module';
import { StudentsModule } from './modules/students/students.module';

@Module({
	controllers: [AppController],
	imports: [
		ConfigModule.forRoot({
			isGlobal: true,
		}),
		PrismaModule,
		AuthModule,
		StudentsModule,
		DocumentsModule,
		OnboardingModule,
		ExamsModule,
		HintsModule,
		PracticeModule,
		HistoryModule,
	],
})
export class AppModule { }
