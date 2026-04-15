import {
	BadRequestException,
	Injectable,
	UnauthorizedException,
} from '@nestjs/common';
import { Student } from '@prisma/client';
import { ConfigService } from '@nestjs/config';
import { JwtService } from '@nestjs/jwt';
import * as bcrypt from 'bcrypt';
import { OAuth2Client } from 'google-auth-library';
import { PrismaService } from 'src/infrastructure/prisma/prisma.service';
import { toStudentResponse } from 'src/modules/students/student-response';
import { GoogleLoginDto } from './dto/google-login.dto';
import { LoginDto } from './dto/login.dto';
import { RegisterDto } from './dto/register.dto';
import { JwtPayload } from 'src/shared/auth/jwt-payload.type';

@Injectable()
export class AuthService {
	private readonly googleClient = new OAuth2Client();

	constructor(
		private readonly prisma: PrismaService,
		private readonly jwtService: JwtService,
		private readonly configService: ConfigService,
	) { }

	private normalizeEmail(email: string) {
		return email.trim().toLowerCase();
	}

	private async issueAuthResponse(student: Student) {
		const payload: JwtPayload = {
			sub: student.id,
			email: student.email,
		};

		return {
			access_token: await this.jwtService.signAsync(payload),
			student: toStudentResponse(student),
		};
	}

	private async verifyGoogleCredential(credential: string) {
		const googleClientId = this.configService.get<string>('GOOGLE_CLIENT_ID');
		if (!googleClientId) {
			throw new UnauthorizedException('Google login chưa được cấu hình');
		}

		try {
			const ticket = await this.googleClient.verifyIdToken({
				idToken: credential,
				audience: googleClientId,
			});
			const payload = ticket.getPayload();
			const email = payload?.email ? this.normalizeEmail(payload.email) : '';

			if (!payload?.sub || !email || payload.email_verified === false) {
				throw new UnauthorizedException('Không xác thực được tài khoản Google');
			}

			return {
				sub: payload.sub,
				email,
				name: payload.name?.trim() || null,
			};
		} catch (error) {
			if (error instanceof UnauthorizedException) {
				throw error;
			}

			throw new UnauthorizedException('Không xác thực được tài khoản Google');
		}
	}

	async register(dto: RegisterDto) {
		if (dto.password !== dto.confirm_password) {
			throw new BadRequestException('Mật khẩu xác nhận không khớp');
		}

		const email = this.normalizeEmail(dto.email);
		const existing = await this.prisma.student.findUnique({
			where: { email },
		});

		if (existing) {
			throw new BadRequestException('Email đã tồn tại');
		}

		const passwordHash = await bcrypt.hash(dto.password, 10);
		const student = await this.prisma.student.create({
			data: {
				name: null,
				email,
				grade: null,
				school: null,
				learning_goal: null,
				profile_completed: false,
				google_sub: null,
				password_hash: passwordHash,
			},
		});

		return {
			student: toStudentResponse(student),
		};
	}

	async login(dto: LoginDto) {
		const email = this.normalizeEmail(dto.email);
		const student = await this.prisma.student.findUnique({
			where: { email },
		});

		if (!student) {
			throw new UnauthorizedException('Thông tin đăng nhập không đúng');
		}

		if (!student.password_hash) {
			throw new UnauthorizedException('Thông tin đăng nhập không đúng');
		}

		const passwordMatch = await bcrypt.compare(dto.password, student.password_hash);
		if (!passwordMatch) {
			throw new UnauthorizedException('Thông tin đăng nhập không đúng');
		}

		return this.issueAuthResponse(student);
	}

	async loginWithGoogle(dto: GoogleLoginDto) {
		const googleProfile = await this.verifyGoogleCredential(dto.credential);
		const linkedByGoogle = await this.prisma.student.findFirst({
			where: { google_sub: googleProfile.sub },
		});

		if (linkedByGoogle) {
			return this.issueAuthResponse(linkedByGoogle);
		}

		const linkedByEmail = await this.prisma.student.findUnique({
			where: { email: googleProfile.email },
		});
		const student = linkedByEmail
			? await this.prisma.student.update({
				where: { id: linkedByEmail.id },
				data: {
					google_sub: googleProfile.sub,
					name: linkedByEmail.name ?? googleProfile.name,
				},
			})
			: await this.prisma.student.create({
				data: {
					email: googleProfile.email,
					google_sub: googleProfile.sub,
					name: googleProfile.name,
					password_hash: null,
					grade: null,
					school: null,
					learning_goal: null,
					profile_completed: false,
				},
			});

		return this.issueAuthResponse(student);
	}
}
