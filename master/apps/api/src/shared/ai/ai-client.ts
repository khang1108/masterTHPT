import { Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';

const logger = new Logger('AiClient');

export function getAiApiUrl(configService: ConfigService) {
	return configService.get<string>('AI_API_BASE_URL')?.trim();
}

function safeStringify(value: unknown) {
	try {
		return JSON.stringify(value);
	} catch {
		return '[unserializable-payload]';
	}
}

function truncateForLog(value: string, maxLength = 2000) {
	if (value.length <= maxLength) {
		return value;
	}

	return `${value.slice(0, maxLength)}... [truncated ${value.length - maxLength} chars]`;
}

export async function postToAiService<TResponse>(
	configService: ConfigService,
	payload: unknown,
) {
	// Centralizing outbound AI calls keeps error handling and request shape changes
	// in one place as more intents are added over time.
	const aiApiUrl = getAiApiUrl(configService);
	if (!aiApiUrl) {
		logger.warn(
			`Skipping AI request because AI_API_BASE_URL is empty. payload=${truncateForLog(safeStringify(payload))}`,
		);
		return null;
	}

	const requestBody = safeStringify(payload);
	logger.log(
		`Sending AI request: url=${aiApiUrl} payload=${truncateForLog(requestBody)}`,
	);

	const response = await fetch(aiApiUrl, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
		},
		body: requestBody,
	});

	logger.log(`AI response received: status=${response.status} url=${aiApiUrl}`);

	if (!response.ok) {
		throw new Error(`AI service returned ${response.status}`);
	}

	// Most current intents return JSON bodies, so the helper returns parsed data directly.
	// If one future intent needs a different content type, extend this helper rather than
	// reintroducing ad-hoc fetch calls in feature services.
	return response.json() as Promise<TResponse>;
}
