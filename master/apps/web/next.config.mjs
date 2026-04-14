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
};

export default nextConfig;
