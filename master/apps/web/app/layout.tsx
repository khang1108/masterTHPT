import 'katex/dist/katex.min.css';
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import Script from 'next/script';
import './globals.css';

const inter = Inter({
	subsets: ['latin'],
	display: 'swap',
});

export const metadata: Metadata = {
	title: 'MASTER THPT',
	description: 'Auth flow for MASTER THPT',
};

export default function RootLayout({
	children,
}: Readonly<{
	children: React.ReactNode;
}>) {
	return (
		<html lang="en">
			<body className={inter.className}>
				<Script src="https://accounts.google.com/gsi/client" strategy="afterInteractive" />
				{children}
			</body>
		</html>
	);
}
