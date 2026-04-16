'use client';

import { GoogleLoginButton } from '@/features/auth/components/google-login-button';
import { login, loginWithGoogle } from '@/shared/api/client';
import { getToken, saveAuth } from '@/shared/auth/storage';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { FormEvent, useEffect, useState } from 'react';

function getErrorMessage(error: unknown) {
	if (typeof error === 'object' && error !== null && 'response' in error) {
		const maybeResponse = error as {
			response?: { data?: { message?: string | string[] } };
		};

		const message = maybeResponse.response?.data?.message;
		if (Array.isArray(message)) {
			return message[0] ?? 'Login failed';
		}

		if (typeof message === 'string') {
			return message;
		}
	}

	return 'Login failed. Please try again.';
}

export default function LoginPage() {
	const router = useRouter();
	const [email, setEmail] = useState('');
	const [password, setPassword] = useState('');
	const [error, setError] = useState('');
	const [loading, setLoading] = useState(false);
	const [googleLoading, setGoogleLoading] = useState(false);

	useEffect(() => {
		if (getToken()) {
			router.replace('/dashboard');
		}
	}, [router]);

	async function onSubmit(event: FormEvent<HTMLFormElement>) {
		event.preventDefault();
		setError('');
		setLoading(true);

		try {
			const data = await login({ email, password });
			saveAuth(data.access_token, data.student);
			router.replace('/dashboard');
		} catch (err: unknown) {
			setError(getErrorMessage(err));
		} finally {
			setLoading(false);
		}
	}

	async function onGoogleCredential(credential: string) {
		setError('');
		setGoogleLoading(true);

		try {
			const data = await loginWithGoogle({ credential });
			saveAuth(data.access_token, data.student);
			router.replace('/dashboard');
		} catch (err: unknown) {
			setError(getErrorMessage(err));
		} finally {
			setGoogleLoading(false);
		}
	}

	return (
		<main className="auth-page">
			<section className="auth-grid">
				<aside className="auth-hero">
					<div>
						<p className="auth-kicker">Nền tảng ôn luyện thông minh</p>
						<h1 className="auth-title">MASTER THPT</h1>
						<p className="auth-copy">
							MASTER THPT giúp bạn luyện đề theo năng lực cá nhân, mô phỏng phòng
							thi thực tế và nhận phân tích chi tiết sau mỗi bài làm.
						</p>
					</div>
				</aside>

				<div className="auth-form-wrap">
					<h2>Đăng nhập</h2>

					<form className="auth-form" onSubmit={onSubmit}>
						<label className="input-label" htmlFor="email">
							Email
						</label>
						<input
							id="email"
							type="email"
							className="input-field"
							value={email}
							onChange={(event) => setEmail(event.target.value)}
							required
						/>

						<label className="input-label" htmlFor="password">
							Mật khẩu
						</label>
						<input
							id="password"
							type="password"
							className="input-field"
							value={password}
							onChange={(event) => setPassword(event.target.value)}
							minLength={6}
							required
						/>

						{error ? <p className="error-text">{error}</p> : null}

						<button className="btn-primary" type="submit" disabled={loading}>
							{loading ? 'Đang đăng nhập...' : 'Đăng nhập'}
						</button>
					</form>

					<div className="auth-divider" aria-hidden="true">
						<span>hoặc</span>
					</div>

					<GoogleLoginButton
						label="Tiếp tục với Google"
						loading={googleLoading}
						onCredential={onGoogleCredential}
					/>

					<p className="muted-link">
						Chưa có tài khoản? <Link href="/register">Tạo tài khoản</Link>
					</p>
				</div>
			</section>
		</main>
	);
}
