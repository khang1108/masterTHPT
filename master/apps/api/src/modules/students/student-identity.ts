import { NotFoundException } from '@nestjs/common';
import { Student } from '@prisma/client';
import { PrismaService } from 'src/infrastructure/prisma/prisma.service';

function isMongoObjectId(value: string) {
	return /^[a-f0-9]{24}$/i.test(value);
}

export async function findStudentByIdentity(
	prisma: PrismaService,
	identity: string,
): Promise<Student | null> {
	const normalizedIdentity = identity.trim();
	if (!normalizedIdentity) {
		return null;
	}

	return prisma.student.findFirst({
		where: {
			OR: [
				{ user_id: normalizedIdentity },
				...(isMongoObjectId(normalizedIdentity) ? [{ mongo_id: normalizedIdentity }] : []),
			],
		},
	});
}

export async function requireStudentByIdentity(
	prisma: PrismaService,
	identity: string,
	errorMessage = 'Không tìm thấy tài khoản học sinh',
): Promise<Student> {
	const student = await findStudentByIdentity(prisma, identity);
	if (!student) {
		throw new NotFoundException(errorMessage);
	}

	return student;
}
