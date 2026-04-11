'use client';

import { register } from '@/lib/api';
import { getToken } from '@/lib/auth';
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
			return message[0] ?? 'Register failed';
		}

		if (typeof message === 'string') {
			return message;
		}
	}

	return 'Register failed. Please try again.';
}

export default function RegisterPage() {
	const router = useRouter();
	const [name, setName] = useState('');
	const [email, setEmail] = useState('');
	const [password, setPassword] = useState('');
	const [grade, setGrade] = useState(12);
	const [error, setError] = useState('');
	const [loading, setLoading] = useState(false);

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
				name,
				email,
				password,
				grade,
			});
			router.replace('/login');
		} catch (err: unknown) {
			setError(getErrorMessage(err));
		} finally {
			setLoading(false);
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
					<h2>Register</h2>
					<form className="auth-form" onSubmit={onSubmit}>
						<label className="input-label" htmlFor="name">
							Họ và Tên
						</label>
						<input
							id="name"
							type="text"
							className="input-field"
							value={name}
							onChange={(e) => setName(e.target.value)}
							required
						/>

						<label className="input-label" htmlFor="email">
							Email
						</label>
						<input
							id="email"
							type="email"
							className="input-field"
							value={email}
							onChange={(e) => setEmail(e.target.value)}
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
									onChange={(e) => setPassword(e.target.value)}
									minLength={6}
									required
								/>
							</div>
							<div>
								<label className="input-label" htmlFor="grade">
									Lớp (10-12)
								</label>
								<input
									id="grade"
									type="number"
									className="input-field"
									min={10}
									max={12}
									value={grade}
									onChange={(e) => setGrade(Number(e.target.value))}
									required
								/>
							</div>
						</div>

						{error ? <p className="error-text">{error}</p> : null}

						<button className="btn-primary" type="submit" disabled={loading}>
							{loading ? 'Tạo tài khoản...' : 'Đăng ký'}
						</button>
					</form>

					<p className="muted-link">
						Đã có tài khoản? <Link href="/login">Đăng nhập</Link>
					</p>
				</div>
			</section>
		</main>
	);
}
