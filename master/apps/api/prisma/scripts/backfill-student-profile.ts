import { PrismaClient } from '@prisma/client';
import { hasCompletedProfile } from '../../src/modules/students/student-profile-state';

const prisma = new PrismaClient();

async function main() {
	const students = await prisma.student.findMany();

	for (const student of students) {
		await prisma.student.update({
			where: { id: student.id },
			data: {
				profile_completed: hasCompletedProfile(student),
			},
		});
	}
}

main()
	.catch((error) => {
		console.error('Failed to backfill student profiles', error);
		process.exitCode = 1;
	})
	.finally(async () => {
		await prisma.$disconnect();
	});
