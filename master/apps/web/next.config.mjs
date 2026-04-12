/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true,
    output: 'standalone',

    async rewrites() {
        return [
            {
                source: '/:path*',
                
                destination: 'http://api:3001/api/:path*', 
            },
        ];
    },
};

export default nextConfig;