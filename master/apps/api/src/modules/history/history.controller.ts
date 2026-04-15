import { Body, Controller, Get, Param, Post, UseGuards } from '@nestjs/common';
import { JwtPayload } from 'src/shared/auth/jwt-payload.type';
import { CurrentUser } from 'src/shared/decorators/current-user.decorator';
import { JwtAuthGuard } from 'src/shared/guards/jwt-auth.guard';
import { CreateHistoryDto } from './dto/create-history.dto';
import { HistoryService } from './history.service';

@Controller('history')
@UseGuards(JwtAuthGuard)
export class HistoryController {
	constructor(private readonly historyService: HistoryService) { }

	@Get()
	list(@CurrentUser() user: JwtPayload) {
		return this.historyService.list(user.sub);
	}

	@Get(':id')
	getDetail(@CurrentUser() user: JwtPayload, @Param('id') id: string) {
		return this.historyService.getDetail(user.sub, id);
	}

	@Post()
	create(@CurrentUser() user: JwtPayload, @Body() dto: CreateHistoryDto) {
		return this.historyService.create(user.sub, dto);
	}
}
