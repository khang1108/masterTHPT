function normalizeApiProxyTarget(value) {
	if (!value) {
		return '';
	}

	return value.replace(/\/$/, '').replace(/\/api$/, '');
}

const apiProxyTarget = normalizeApiProxyTarget(process.env.API_PROXY_TARGET);

/** @type {import('next').NextConfig} */
const nextConfig = {
	reactStrictMode: true,
	output: 'standalone',

	images: {
		remotePatterns: [
			{
				protocol: 'https',
				hostname: 'drive.google.com',
				pathname: '/uc/**',
			},
		],
	},

	async rewrites() {
		if (!apiProxyTarget) {
			return [];
		}

		return [
			{
				source: '/:path*',
				destination: `${apiProxyTarget}/:path*`,
			},
		];
	},
};

export default nextConfig;
