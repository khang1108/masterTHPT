import { Injectable, Logger, OnModuleInit } from '@nestjs/common';
import { randomUUID } from 'crypto';
import { PrismaClient } from '@prisma/client';

@Injectable()
export class PrismaService extends PrismaClient implements OnModuleInit {
	private readonly logger = new Logger(PrismaService.name);

	async onModuleInit() {
		await this.$connect();
		await this.initializeMongoSchema();
	}

	private isPlainObject(value: unknown): value is Record<string, unknown> {
		return typeof value === 'object' && value !== null && !Array.isArray(value);
	}

	private extractFirstBatch(result: unknown) {
		if (!this.isPlainObject(result)) {
			return [];
		}

		const cursor = result.cursor;
		if (!this.isPlainObject(cursor) || !Array.isArray(cursor.firstBatch)) {
			return [];
		}

		return cursor.firstBatch.filter((item): item is Record<string, unknown> => this.isPlainObject(item));
	}

	private toMongoId(value: unknown) {
		if (typeof value === 'string' && value.trim().length > 0) {
			return value;
		}

		if (this.isPlainObject(value) && typeof value.$oid === 'string' && value.$oid.trim().length > 0) {
			return value.$oid;
		}

		return null;
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

		await this.backfillStudentUserIds();
		await this.backfillQuestionIds();

		await this.$runCommandRaw({
			createIndexes: 'students',
			indexes: [
				{
					key: { email: 1 },
					name: 'students_email_key',
					unique: true,
				},
				{
					key: { user_id: 1 },
					name: 'students_user_id_key',
					unique: true,
				},
			],
		});

		await this.ensureQuestionIndexes();

		this.logger.log('Mongo schema bootstrap completed');
	}

	private async backfillStudentUserIds() {
		const result = await this.$runCommandRaw({
			find: 'students',
			filter: {},
			projection: {
				_id: 1,
				user_id: 1,
			},
		});
		const students = this.extractFirstBatch(result);

		for (const student of students) {
			const mongoId = this.toMongoId(student._id);
			if (!mongoId) {
				continue;
			}

			const existingUserId =
				typeof student.user_id === 'string' && student.user_id.trim().length > 0
					? student.user_id.trim()
					: randomUUID();

			if (student.user_id !== existingUserId) {
				await this.$runCommandRaw({
					update: 'students',
					updates: [
						{
							q: { _id: { $oid: mongoId } },
							u: { $set: { user_id: existingUserId } },
						},
					],
				});
			}

			await this.$runCommandRaw({
				update: 'practices',
				updates: [
					{
						q: { user_id: mongoId },
						u: { $set: { user_id: existingUserId } },
						multi: true,
					},
				],
			});

			await this.$runCommandRaw({
				update: 'histories',
				updates: [
					{
						q: { user_id: mongoId },
						u: { $set: { user_id: existingUserId } },
						multi: true,
					},
				],
			});
		}
	}

	private async backfillQuestionIds() {
		const result = await this.$runCommandRaw({
			find: 'questions',
			filter: {
				$or: [
					{ question_id: { $exists: false } },
					{ question_id: null },
					{ question_id: '' },
				],
			},
			projection: {
				_id: 1,
				id: 1,
				question_id: 1,
			},
		});
		const questions = this.extractFirstBatch(result);

		for (const question of questions) {
			const mongoId = this.toMongoId(question._id);
			const legacyId = typeof question.id === 'string' && question.id.trim().length > 0
				? question.id.trim()
				: null;

			if (!mongoId || !legacyId) {
				continue;
			}

			await this.$runCommandRaw({
				update: 'questions',
				updates: [
					{
						q: { _id: { $oid: mongoId } },
						u: { $set: { question_id: legacyId } },
					},
				],
			});
		}
	}

	private async ensureQuestionIndexes() {
		try {
			await this.$runCommandRaw({
				createIndexes: 'questions',
				indexes: [
					{
						key: { question_id: 1 },
						name: 'questions_question_id_key',
						unique: true,
					},
				],
			});
		} catch (error) {
			if (!this.isIgnorableMongoError(error, ['IndexOptionsConflict', 'IndexKeySpecsConflict'], [85, 86])) {
				throw error;
			}
		}
	}
}
