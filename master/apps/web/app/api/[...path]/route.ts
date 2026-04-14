import { NextRequest } from 'next/server';

export const runtime = 'nodejs';

function normalizeProxyTarget(value?: string) {
	if (!value) {
		return '';
	}

	return value.replace(/\/$/, '').replace(/\/api$/, '');
}

function buildProxyUrl(request: NextRequest, path: string[]) {
	const proxyTarget = normalizeProxyTarget(process.env.API_PROXY_TARGET);
	if (!proxyTarget) {
		throw new Error('API_PROXY_TARGET is not configured.');
	}

	const requestUrl = new URL(request.url);
	const joinedPath = path.join('/');
	const search = requestUrl.search || '';

	return `${proxyTarget}/api/${joinedPath}${search}`;
}

function cloneHeaders(request: NextRequest) {
	const headers = new Headers(request.headers);

	// These hop-by-hop headers should not be forwarded by the proxy layer.
	headers.delete('host');
	headers.delete('connection');
	headers.delete('content-length');

	return headers;
}

async function forwardRequest(request: NextRequest, context: { params: { path: string[] } }) {
	try {
		const targetUrl = buildProxyUrl(request, context.params.path);
		const method = request.method.toUpperCase();
		const headers = cloneHeaders(request);
		const hasBody = method !== 'GET' && method !== 'HEAD';
		const body = hasBody ? await request.arrayBuffer() : undefined;

		const upstreamResponse = await fetch(targetUrl, {
			method,
			headers,
			body,
			cache: 'no-store',
			redirect: 'manual',
		});

		const responseHeaders = new Headers(upstreamResponse.headers);
		responseHeaders.delete('content-length');
		responseHeaders.delete('transfer-encoding');
		responseHeaders.delete('connection');

		return new Response(upstreamResponse.body, {
			status: upstreamResponse.status,
			statusText: upstreamResponse.statusText,
			headers: responseHeaders,
		});
	} catch (error) {
		const message = error instanceof Error ? error.message : 'Unable to reach backend service.';
		return Response.json(
			{
				message,
				error: 'Bad Gateway',
				statusCode: 502,
			},
			{ status: 502 },
		);
	}
}

export async function GET(request: NextRequest, context: { params: { path: string[] } }) {
	return forwardRequest(request, context);
}

export async function POST(request: NextRequest, context: { params: { path: string[] } }) {
	return forwardRequest(request, context);
}

export async function PUT(request: NextRequest, context: { params: { path: string[] } }) {
	return forwardRequest(request, context);
}

export async function PATCH(request: NextRequest, context: { params: { path: string[] } }) {
	return forwardRequest(request, context);
}

export async function DELETE(request: NextRequest, context: { params: { path: string[] } }) {
	return forwardRequest(request, context);
}

export async function OPTIONS(request: NextRequest, context: { params: { path: string[] } }) {
	return forwardRequest(request, context);
}
