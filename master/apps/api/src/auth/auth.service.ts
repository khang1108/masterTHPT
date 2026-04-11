import {
	BadRequestException,
	Injectable,
	UnauthorizedException,
} from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import * as bcrypt from 'bcrypt';
import { PrismaService } from 'src/prisma/prisma.service';
import { LoginDto } from './dto/login.dto';
import { RegisterDto } from './dto/register.dto';
import { JwtPayload } from './types';

@Injectable()
export class AuthService {
	constructor(
		private readonly prisma: PrismaService,
		private readonly jwtService: JwtService,
	) { }

	async register(dto: RegisterDto) {
		const existing = await this.prisma.student.findUnique({
			where: { email: dto.email },
		});

		if (existing) {
			throw new BadRequestException('Email đã tồn tại');
		}

		const passwordHash = await bcrypt.hash(dto.password, 10);

		const student = await this.prisma.student.create({
			data: {
				name: dto.name,
				email: dto.email,
				grade: dto.grade,
				password_hash: passwordHash,
			},
		});


		return {
			student: {
				id: student.id,
				name: student.name,
				email: student.email,
				grade: student.grade,
				is_first_login: student.is_first_login,
			},
		};
	}

	async login(dto: LoginDto) {
		const student = await this.prisma.student.findUnique({
			where: { email: dto.email },
		});

		if (!student) {
			throw new UnauthorizedException('Thông tin đăng nhập không đúng');
		}

		const passwordMatch = await bcrypt.compare(dto.password, student.password_hash);
		if (!passwordMatch) {
			throw new UnauthorizedException('Thông tin đăng nhập không đúng');
		}

		const payload: JwtPayload = {
			sub: student.id,
			email: student.email,
			name: student.name,
			grade: student.grade,
		};

		return {
			access_token: await this.jwtService.signAsync(payload),
			student: {
				id: student.id,
				name: student.name,
				email: student.email,
				grade: student.grade,
				is_first_login: student.is_first_login,
			},
		};
	}
}
