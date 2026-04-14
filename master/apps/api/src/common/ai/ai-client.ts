import { ConfigService } from '@nestjs/config';

export function getAiApiUrl(configService: ConfigService) {
	return configService.get<string>('AI_API_BASE_URL')?.trim();
}

export async function postToAiService<TResponse>(
	configService: ConfigService,
	payload: unknown,
) {
	// Centralizing outbound AI calls keeps error handling and request shape changes
	// in one place as more intents are added over time.
	const aiApiUrl = getAiApiUrl(configService);
	if (!aiApiUrl) {
		return null;
	}

	const response = await fetch(aiApiUrl, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
		},
		body: JSON.stringify(payload),
	});

	if (!response.ok) {
		throw new Error(`AI service returned ${response.status}`);
	}

	// Most current intents return JSON bodies, so the helper returns parsed data directly.
	// If one future intent needs a different content type, extend this helper rather than
	// reintroducing ad-hoc fetch calls in feature services.
	return response.json() as Promise<TResponse>;
}
