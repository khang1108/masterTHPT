import { BadGatewayException, Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { DocumentItem, ExamDetail } from 'src/mocks/types';

type RequestOptions = {
	method?: 'GET' | 'POST';
	body?: unknown;
};

@Injectable()
export class ExternalApiService {
	constructor(private readonly configService: ConfigService) { }

	isMockEnabled(): boolean {
		const value = this.configService.get<string>('USE_MOCK_SERVICES', 'true');
		return value.toLowerCase() !== 'false';
	}

	private normalizeBaseUrl(baseUrl: string | undefined): string | null {
		if (!baseUrl) {
			return null;
		}

		const trimmed = baseUrl.trim();
		if (trimmed.length === 0) {
			return null;
		}

		return trimmed.replace(/\/+$/, '');
	}

	private getRequiredPath(key: string, defaultValue: string): string {
		const value = this.configService.get<string>(key, defaultValue).trim();
		if (value.length === 0) {
			throw new BadGatewayException(`Missing or empty path config: ${key}`);
		}

		return value;
	}

	private resolvePath(template: string, params: Record<string, string> = {}) {
		let path = template;
		for (const [key, value] of Object.entries(params)) {
			path = path.replace(`:${key}`, encodeURIComponent(value));
		}

		if (!path.startsWith('/')) {
			return `/${path}`;
		}

		return path;
	}

	private async requestJson<T>(url: string, options: RequestOptions = {}): Promise<T> {
		const response = await fetch(url, {
			method: options.method ?? 'GET',
			headers: {
				'Content-Type': 'application/json',
			},
			body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
		});

		if (!response.ok) {
			const message = await response.text();
			throw new BadGatewayException(
				`External API call failed (${response.status}): ${message || 'No message'}`,
			);
		}

		return (await response.json()) as T;
	}

	async listDocuments(): Promise<DocumentItem[] | null> {
		const baseUrl = this.normalizeBaseUrl(this.configService.get<string>('AI_API_BASE_URL'));
		if (!baseUrl) {
			if (!this.isMockEnabled()) {
				throw new BadGatewayException(
					'Missing AI_API_BASE_URL while USE_MOCK_SERVICES=false',
				);
			}

			return null;
		}

		const path = this.getRequiredPath('AI_API_DOCUMENTS_PATH', '/documents');
		return this.requestJson<DocumentItem[]>(`${baseUrl}${this.resolvePath(path)}`);
	}

	async getExamByDocumentId(documentId: string): Promise<ExamDetail | null> {
		const baseUrl = this.normalizeBaseUrl(this.configService.get<string>('AI_API_BASE_URL'));
		if (!baseUrl) {
			if (!this.isMockEnabled()) {
				throw new BadGatewayException(
					'Missing AI_API_BASE_URL while USE_MOCK_SERVICES=false',
				);
			}

			return null;
		}

		const pathTemplate = this.getRequiredPath(
			'AI_API_EXAM_BY_DOCUMENT_PATH',
			'/documents/:id',
		);
		const path = this.resolvePath(pathTemplate, { id: documentId });

		return this.requestJson<ExamDetail>(`${baseUrl}${path}`);
	}

	async generateExam(payload: {
		uuid?: string;
		sourceType: string;
		subject?: string;
		examType?: string;
		embeddedText?: string;
		subjects?: Array<{
			subject: string;
			scores: Array<{
				label: string;
				value: string;
			}>;
		}>;
	}): Promise<ExamDetail | null> {
		const baseUrl = this.normalizeBaseUrl(this.configService.get<string>('AI_API_BASE_URL'));
		if (!baseUrl) {
			if (!this.isMockEnabled()) {
				throw new BadGatewayException(
					'Missing AI_API_BASE_URL while USE_MOCK_SERVICES=false',
				);
			}

			return null;
		}

		const path = this.getRequiredPath('AI_API_GENERATE_EXAM_PATH', '/manager');
		return this.requestJson<ExamDetail>(`${baseUrl}${this.resolvePath(path)}`, {
			method: 'POST',
			body: payload,
		});
	}

	async evaluateExam(payload: unknown): Promise<unknown | null> {
		const baseUrl = this.normalizeBaseUrl(this.configService.get<string>('AI_API_BASE_URL'));
		if (!baseUrl) {
			if (!this.isMockEnabled()) {
				throw new BadGatewayException(
					'Missing AI_API_BASE_URL while USE_MOCK_SERVICES=false',
				);
			}

			return null;
		}

		const path = this.getRequiredPath('AI_API_EVALUATE_EXAM_PATH', '/manager');
		return this.requestJson<unknown>(`${baseUrl}${this.resolvePath(path)}`, {
			method: 'POST',
			body: payload,
		});
	}
}
