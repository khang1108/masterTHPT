'use client';

import { PracticeExamItem, getPracticeExams, updatePractice } from '@/lib/api';
import { getToken } from '@/lib/auth';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from 'react';

function formatPracticePrimaryMetric(item: PracticeExamItem) {
	return `${item.total_questions} câu • Lớp ${item.grade}`;
}

export default function PracticePage() {
	const router = useRouter();
	const textareaRef = useRef<HTMLTextAreaElement | null>(null);
	const [items, setItems] = useState<PracticeExamItem[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState('');
	const [requestText, setRequestText] = useState('');
	const [isUpdating, setIsUpdating] = useState(false);
	const [updateError, setUpdateError] = useState('');

	async function loadPracticeExams(authToken: string) {
		setLoading(true);
		setError('');

		try {
			const data = await getPracticeExams(authToken);
			setItems(data);
		} catch {
			setError('Không thể tải danh sách bài luyện tập. Vui lòng thử lại.');
		} finally {
			setLoading(false);
		}
	}

	useEffect(() => {
		const storedToken = getToken();
		if (!storedToken) {
			router.replace('/login');
			return;
		}

		loadPracticeExams(storedToken);
	}, [router]);

	useEffect(() => {
		const textarea = textareaRef.current;
		if (!textarea) {
			return;
		}

		textarea.style.height = '0px';
		const nextHeight = Math.min(textarea.scrollHeight, 128);
		textarea.style.height = `${Math.max(nextHeight, 48)}px`;
	}, [requestText]);

	async function submitPracticeUpdate() {
		const trimmedRequest = requestText.trim();
		if (!trimmedRequest || isUpdating) {
			return;
		}

		const token = getToken();
		if (!token) {
			router.replace('/login');
			return;
		}

		setUpdateError('');
		setIsUpdating(true);

		try {
			await updatePractice(token, {
				request: trimmedRequest,
			});
			await loadPracticeExams(token);
			setRequestText('');
		} catch {
			setUpdateError('Không thể gửi yêu cầu cập nhật lúc này. Vui lòng thử lại.');
		} finally {
			setIsUpdating(false);
		}
	}

	async function onSubmitUpdate(event: FormEvent<HTMLFormElement>) {
		event.preventDefault();
		await submitPracticeUpdate();
	}

	function onComposerKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
		if (event.key !== 'Enter' || event.shiftKey) {
			return;
		}

		event.preventDefault();

		if (!requestText.trim() || isUpdating) {
			return;
		}

		void submitPracticeUpdate();
	}

	return (
		<main className="documents-page practice-page">
			<header className="documents-header">
				<div>
					<p className="documents-kicker">Phòng luyện thi</p>
					<h1 className="documents-title">Trang luyện tập</h1>
					<p className="text-soft">Danh sách đề đang được gán riêng cho tài khoản của bạn, có thể cập nhật lại bằng yêu cầu mới.</p>
				</div>
				<Link href="/dashboard" className="btn-ghost">
					Quay lại tổng quan
				</Link>
			</header>

			{isUpdating ? (
				<p className="documents-message practice-status" role="status" aria-live="polite">
					Đang cập nhật danh sách đề luyện tập...
				</p>
			) : null}

			{loading ? <p className="documents-message">Đang tải danh sách luyện tập...</p> : null}
			{!loading && error ? <p className="documents-error">{error}</p> : null}

			{!loading && !error ? (
				<>
					<p className="documents-count">
						Có {items.length} đề luyện tập dành cho bạn
					</p>
					<section className="documents-grid">
						{items.map((item) => (
							<article key={item.id} className="documents-card">
								<div className="documents-card-top">
									<p className="documents-card-type">{item.exam_type}</p>
									<h2 className="documents-card-title">
										{item.subject} - {item.exam_type}
									</h2>
									<p className="documents-card-stat">{formatPracticePrimaryMetric(item)}</p>
									<p className="documents-card-meta">
										{item.source} • Năm {item.year}
									</p>
									<p className="documents-card-submeta">Mã đề: {item.id}</p>
								</div>
								<div className="documents-card-bottom">
									<div className="documents-tags">
										<span className="documents-tag">Luyện tập cá nhân</span>
									</div>
									<div className="documents-card-actions">
										<Link href={`/exams/${item.id}?intent=practice`} className="btn-primary documents-start-btn">
											Luyện ngay
										</Link>
									</div>
								</div>
							</article>
						))}
					</section>

					{items.length === 0 ? (
						<section className="documents-empty" aria-live="polite">
							Hiện chưa có đề luyện tập nào được gán cho bạn.
						</section>
					) : null}
				</>
			) : null}

			<div className="practice-composer-dock">
				<form className="practice-composer-shell" onSubmit={onSubmitUpdate}>
					<textarea
						ref={textareaRef}
						className="practice-composer-input"
						placeholder="Nhập mong muốn luyện tập của bạn..."
						value={requestText}
						onChange={(event) => setRequestText(event.target.value)}
						onKeyDown={onComposerKeyDown}
						disabled={isUpdating}
						rows={1}
					/>
					<button
						type="submit"
						className="practice-composer-send"
						disabled={!requestText.trim() || isUpdating}
						aria-label={isUpdating ? 'Đang gửi yêu cầu cập nhật' : 'Gửi yêu cầu cập nhật'}
					>
						{isUpdating ? (
							<span className="exam-submit-spinner practice-composer-spinner" aria-hidden="true" />
						) : (
							<svg viewBox="0 0 24 24" aria-hidden="true" className="practice-composer-icon">
								<path
									d="M4 12.75L19.2 4.6c.6-.32 1.3.2 1.16.88l-2.33 11.44a1 1 0 01-.8.79L5.8 19.95c-.69.14-1.22-.58-.88-1.18l2.92-5.17a1 1 0 000-.98L4.92 7.45c-.34-.6.2-1.32.88-1.18"
									fill="currentColor"
								/>
							</svg>
						)}
					</button>
				</form>
				{updateError ? <p className="documents-error practice-composer-error">{updateError}</p> : null}
			</div>
		</main>
	);
}
