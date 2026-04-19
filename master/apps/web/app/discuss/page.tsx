'use client';

import { DashboardTopbar } from '@/features/dashboard/components/dashboard-topbar';
import { useAuthenticatedStudentPage } from '@/features/dashboard/lib/use-authenticated-student-page';
import Link from 'next/link';
import { useState } from 'react';

const DISCUSSION_THREADS = [
	{
		category: 'Nhóm Toán 12',
		title: 'Có nên ưu tiên xác suất có điều kiện trước khi ôn tổ hợp không?',
		excerpt: 'Chốt thứ tự ôn để không bị lan man.',
		activity: '28 phản hồi',
	},
	{
		category: 'Chiến lược ôn thi',
		title: 'Cách giữ nhịp học đều khi vừa luyện đề vừa phải hoàn thiện hồ sơ đại học',
		excerpt: 'Chia giờ học và xử lý ngày bị vỡ kế hoạch.',
		activity: '16 phản hồi',
	},
	{
		category: 'Nhóm Văn',
		title: 'Mẫu mở bài nào đủ linh hoạt để dùng cho nhiều dạng nghị luận xã hội?',
		excerpt: 'Tổng hợp mẫu mở bài ngắn, dễ biến đổi.',
		activity: '21 phản hồi',
	},
] as const;

export default function DiscussPage() {
	const { student, loading, error, logout } = useAuthenticatedStudentPage(
		'Không thể tải khu thảo luận lúc này.',
	);
	const [draftTitle, setDraftTitle] = useState('');
	const [draftBody, setDraftBody] = useState('');
	const [draftMessage, setDraftMessage] = useState('');

	function saveDraft() {
		if (!draftTitle.trim() && !draftBody.trim()) {
			setDraftMessage('Điền ít nhất tiêu đề hoặc nội dung để lưu bản nháp.');
			return;
		}

		setDraftMessage('Bản nháp thảo luận đã được lưu trong phiên làm việc hiện tại.');
	}

	if (loading) {
		return <main className="dashboard-root">Đang tải khu thảo luận...</main>;
	}

	if (!student) {
		return (
			<main className="dashboard-root">
				<section className="dash-panel dash-error-panel">
					<h2>Không thể mở khu thảo luận</h2>
					<p className="text-soft">{error || 'Thiếu dữ liệu học sinh để hiển thị nội dung.'}</p>
					<div className="dash-inline-actions">
						<Link href="/dashboard" className="btn-primary">
							Về tổng quan
						</Link>
					</div>
				</section>
			</main>
		);
	}

	return (
		<main className="dashboard-shell info-page">
			<DashboardTopbar student={student} onLogout={logout} />

			<section className="info-main-column info-main-column-solo">
				<section className="dash-panel">
					<div className="dash-panel-head">
						<p className="documents-kicker">Chủ đề gần đây</p>
						<h2>3 chủ đề đang được quan tâm</h2>
					</div>

					<div className="info-thread-list">
						{DISCUSSION_THREADS.map((thread) => (
							<article key={thread.title} className="info-thread-card">
								<div className="info-thread-meta">
									<span className="dash-badge">{thread.category}</span>
									<span>{thread.activity}</span>
								</div>
								<h3>{thread.title}</h3>
								<p>{thread.excerpt}</p>
							</article>
						))}
					</div>
				</section>

				<section className="dash-panel" id="tao-thao-luan">
					<div className="dash-panel-head">
						<p className="documents-kicker">Tạo nhanh</p>
						<h2>Soạn một chủ đề mới</h2>
					</div>

					<div className="contact-form-grid contact-form-grid-compact">
						<div>
							<label className="input-label" htmlFor="discuss-title">
								Tiêu đề
							</label>
							<input
								id="discuss-title"
								className="input-field"
								type="text"
								placeholder="Nhập tiêu đề ngắn"
								value={draftTitle}
								onChange={(event) => setDraftTitle(event.target.value)}
							/>
						</div>

						<div className="contact-form-span">
							<label className="input-label" htmlFor="discuss-body">
								Nội dung
							</label>
							<textarea
								id="discuss-body"
								className="input-field input-textarea input-textarea-compact"
								placeholder="Mô tả ngắn vấn đề bạn đang vướng."
								value={draftBody}
								onChange={(event) => setDraftBody(event.target.value)}
							/>
						</div>
					</div>

					<div className="info-form-actions info-form-actions-compact">
						<button type="button" className="btn-primary" onClick={saveDraft}>
							Lưu nháp
						</button>
					</div>

					{draftMessage ? <p className="profile-success-text">{draftMessage}</p> : null}
				</section>
			</section>
		</main>
	);
}
