'use client';

import { GoogleLoginButton } from '@/features/auth/components/google-login-button';
import { loginWithGoogle, register } from '@/shared/api/client';
import { getApiErrorMessage } from '@/shared/api/error-message';
import { getToken, saveAuth } from '@/shared/auth/storage';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { FormEvent, useEffect, useState } from 'react';

export default function RegisterPage() {
	const router = useRouter();
	const [email, setEmail] = useState('');
	const [password, setPassword] = useState('');
	const [confirmPassword, setConfirmPassword] = useState('');
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
			await register({
				email,
				password,
				confirm_password: confirmPassword,
			});
			router.replace('/login');
		} catch (err: unknown) {
			setError(getApiErrorMessage(err, 'Không thể tạo tài khoản lúc này. Vui lòng thử lại.'));
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
			setError(getApiErrorMessage(err, 'Không thể tiếp tục với Google lúc này. Vui lòng thử lại.'));
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
					<h2>Đăng ký</h2>

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

						<div className="split-2">
							<div>
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
							</div>
							<div>
								<label className="input-label" htmlFor="confirm-password">
									Xác nhận mật khẩu
								</label>
								<input
									id="confirm-password"
									type="password"
									className="input-field"
									value={confirmPassword}
									onChange={(event) => setConfirmPassword(event.target.value)}
									minLength={6}
									required
								/>
							</div>
						</div>

						{error ? <p className="error-text">{error}</p> : null}

						<button className="btn-primary" type="submit" disabled={loading}>
							{loading ? 'Tạo tài khoản...' : 'Đăng ký'}
						</button>
					</form>

					<div className="auth-divider" aria-hidden="true">
						<span>hoặc</span>
					</div>

					<GoogleLoginButton
						label="Vào nhanh bằng Google"
						loading={googleLoading}
						onCredential={onGoogleCredential}
					/>

					<p className="muted-link">
						Đã có tài khoản? <Link href="/login">Đăng nhập</Link>
					</p>
				</div>
			</section>
		</main>
	);
}
