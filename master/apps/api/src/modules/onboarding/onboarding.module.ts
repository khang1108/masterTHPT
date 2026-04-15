import { Module } from '@nestjs/common';
import { PrismaModule } from 'src/infrastructure/prisma/prisma.module';
import { OnboardingController } from './onboarding.controller';
import { OnboardingService } from './onboarding.service';

@Module({
	imports: [PrismaModule],
	controllers: [OnboardingController],
	providers: [OnboardingService],
})
export class OnboardingModule { }
