import { Injectable, Logger, OnModuleInit } from '@nestjs/common';
import { PrismaClient } from '@prisma/client';

@Injectable()
export class PrismaService extends PrismaClient implements OnModuleInit {
	private readonly logger = new Logger(PrismaService.name);

	async onModuleInit() {
		await this.$connect();
		await this.initializeMongoSchema();
	}

	private isIgnorableMongoError(
		error: unknown,
		allowedCodeNames: string[],
		allowedCodes: number[] = [],
	) {
		if (!error || typeof error !== 'object') {
			return false;
		}

		const maybeError = error as {
			codeName?: string;
			code?: number;
			message?: string;
		};

		return (
			(!!maybeError.codeName && allowedCodeNames.includes(maybeError.codeName)) ||
			(typeof maybeError.code === 'number' && allowedCodes.includes(maybeError.code))
		);
	}

	private async initializeMongoSchema() {
		// MongoDB creates the database lazily. This ensures core collection/index exists on first boot.
		try {
			await this.$runCommandRaw({ create: 'students' });
		} catch (error) {
			if (!this.isIgnorableMongoError(error, ['NamespaceExists'], [48])) {
				throw error;
			}
		}

		await this.$runCommandRaw({
			createIndexes: 'students',
			indexes: [
				{
					key: { email: 1 },
					name: 'students_email_key',
					unique: true,
				},
			],
		});

		this.logger.log('Mongo schema bootstrap completed');
	}
}
