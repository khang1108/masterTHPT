import { createParamDecorator, ExecutionContext } from '@nestjs/common';
import { JwtPayload } from 'src/shared/auth/jwt-payload.type';

export const CurrentUser = createParamDecorator(
	(_data: unknown, ctx: ExecutionContext): JwtPayload => {
		const request = ctx.switchToHttp().getRequest();
		return request.user;
	},
);
