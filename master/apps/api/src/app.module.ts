import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { AppController } from './app.controller';
import { AuthModule } from './auth/auth.module';
import { DocumentsModule } from './documents/documents.module';
import { ExamsModule } from './exams/exams.module';
import { HintsModule } from './hints/hints.module';
import { HistoryModule } from './history/history.module';
import { OnboardingModule } from './onboarding/onboarding.module';
import { PracticeModule } from './practice/practice.module';
import { PrismaModule } from './prisma/prisma.module';

@Module({
	controllers: [AppController],
	imports: [
		ConfigModule.forRoot({
			isGlobal: true,
		}),
		PrismaModule,
		AuthModule,
		DocumentsModule,
		OnboardingModule,
		ExamsModule,
		HintsModule,
		PracticeModule,
		HistoryModule,
	],
})
export class AppModule { }
