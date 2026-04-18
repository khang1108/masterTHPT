'use client';

import { useEffect, useRef, useState } from 'react';

declare global {
	interface Window {
		google?: {
			accounts?: {
				id?: {
					initialize: (config: {
						client_id: string;
						callback: (response: { credential?: string }) => void;
						auto_select?: boolean;
					}) => void;
					renderButton: (
						parent: HTMLElement,
						options: {
							theme?: 'outline' | 'filled_blue' | 'filled_black';
							size?: 'large' | 'medium' | 'small';
							text?: 'signin_with' | 'signup_with' | 'continue_with';
							shape?: 'pill' | 'rectangular';
							width?: number;
							logo_alignment?: 'left' | 'center';
						},
					) => void;
				};
			};
		};
	}
}

type GoogleLoginButtonProps = {
	label: string;
	loading: boolean;
	disabled?: boolean;
	onCredential: (credential: string) => void | Promise<void>;
};

export function GoogleLoginButton({
	label,
	loading,
	disabled = false,
	onCredential,
}: GoogleLoginButtonProps) {
	const buttonRef = useRef<HTMLDivElement | null>(null);
	const callbackRef = useRef(onCredential);
	const [renderState, setRenderState] = useState<'waiting' | 'ready' | 'missing'>('waiting');
	const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ?? '';

	useEffect(() => {
		callbackRef.current = onCredential;
	}, [onCredential]);

	useEffect(() => {
		if (!googleClientId) {
			setRenderState('missing');
			return;
		}

		let cancelled = false;
		let intervalId: number | null = null;

		const renderButton = () => {
			if (
				cancelled ||
				!buttonRef.current ||
				!window.google?.accounts?.id
			) {
				return false;
			}

			window.google.accounts.id.initialize({
				client_id: googleClientId,
				callback: async (response) => {
					if (!response.credential || disabled || loading) {
						return;
					}

					await callbackRef.current(response.credential);
				},
			});

			buttonRef.current.innerHTML = '';
			window.google.accounts.id.renderButton(buttonRef.current, {
				theme: 'outline',
				size: 'large',
				text: 'continue_with',
				shape: 'pill',
				width: Math.max(buttonRef.current.clientWidth, 280),
				logo_alignment: 'left',
			});
			setRenderState('ready');

			return true;
		};

		if (!renderButton()) {
			intervalId = window.setInterval(() => {
				if (renderButton() && intervalId) {
					window.clearInterval(intervalId);
				}
			}, 250);
		}

		return () => {
			cancelled = true;
			if (intervalId) {
				window.clearInterval(intervalId);
			}
		};
	}, [disabled, googleClientId, loading]);

	return (
		<div className="auth-google-wrap">
			<div className="auth-google-header">
				<strong>{label}</strong>
				<span>
					Bạn có thể đăng nhập nhanh, hoặc tạo tài khoản mới nếu email chưa tồn tại.
				</span>
			</div>

			{renderState === 'missing' ? (
				<p className="error-text">
					Tính năng đăng nhập với Google hiện chưa sẵn sàng. Vui lòng thử lại sau.
				</p>
			) : (
				<div
					ref={buttonRef}
					className={`auth-google-button-shell ${loading || disabled ? 'is-disabled' : ''}`}
					aria-busy={loading}
				/>
			)}
		</div>
	);
}
