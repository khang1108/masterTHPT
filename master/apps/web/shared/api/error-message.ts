export function getApiErrorMessage(error: unknown, fallback: string) {
	if (typeof error === 'object' && error !== null && 'response' in error) {
		const maybeResponse = error as {
			response?: { data?: { message?: string | string[] } };
		};
		const message = maybeResponse.response?.data?.message;

		if (Array.isArray(message)) {
			return message[0] ?? fallback;
		}

		if (typeof message === 'string' && message.trim()) {
			return message;
		}
	}

	if (error instanceof Error && error.message.trim()) {
		return error.message;
	}

	return fallback;
}
