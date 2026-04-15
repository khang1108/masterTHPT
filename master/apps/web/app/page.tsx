'use client';

import { getToken } from '@/shared/auth/storage';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function HomePage() {
	const router = useRouter();

	useEffect(() => {
		const token = getToken();
		if (token) {
			router.replace('/dashboard');
			return;
		}

		router.replace('/login');
	}, [router]);

	return (
		<main style={{ minHeight: '100dvh', display: 'grid', placeItems: 'center' }}>
			<div className="practice-spinner" />
		</main>
	);
}
