/** @type {import('next').NextConfig} */
const nextConfig = {
	reactStrictMode: true,
	output: 'standalone',
	compress: true,
	async rewrites() {
		const apiUrl = process.env.API_URL || 'http://localhost:3001';
		return [
			{
				source: '/api/:path*',
				destination: `${apiUrl}/api/:path*`,
			},
		];
	},
};

export default nextConfig;
