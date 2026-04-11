import { Module } from '@nestjs/common';
import { MockAiService } from './mock-ai.service';
import { MockCloudService } from './mock-cloud.service';

@Module({
	providers: [MockAiService, MockCloudService],
	exports: [MockAiService, MockCloudService],
})
export class MocksModule { }
