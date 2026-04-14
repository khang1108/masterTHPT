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
		return [
			{
				source: '/:path*',
				destination: 'http://api:3001/:path*'
			},
		];
	},
};

export default nextConfig;