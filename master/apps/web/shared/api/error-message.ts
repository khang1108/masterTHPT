type ApiErrorResponse = {
	response?: {
		data?: {
			message?: string | string[];
		};
		status?: number;
	};
};

function getApiErrorResponse(error: unknown): ApiErrorResponse | null {
	if (typeof error !== 'object' || error === null || !('response' in error)) {
		return null;
	}

	return error as ApiErrorResponse;
}

function getApiErrorStatus(error: unknown) {
	return getApiErrorResponse(error)?.response?.status;
}

function getRawApiErrorMessage(error: unknown) {
	const message = getApiErrorResponse(error)?.response?.data?.message;

	if (Array.isArray(message)) {
		return message[0] ?? '';
	}

	return typeof message === 'string' ? message : '';
}

export function getApiErrorMessage(error: unknown, fallback: string) {
	const message = getRawApiErrorMessage(error);
	if (message.trim()) {
		return message;
	}

	if (error instanceof Error && error.message.trim()) {
		return error.message;
	}

	return fallback;
}

export function isInvalidSessionError(error: unknown) {
	const status = getApiErrorStatus(error);
	if (status === 401) {
		return true;
	}

	if (status !== 404) {
		return false;
	}

	const message = getRawApiErrorMessage(error).toLowerCase();
	return message.includes('không tìm thấy tài khoản học sinh');
}
