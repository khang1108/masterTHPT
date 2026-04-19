'use client';

import { DashboardTopbar } from '@/features/dashboard/components/dashboard-topbar';
import { useAuthenticatedStudentPage } from '@/features/dashboard/lib/use-authenticated-student-page';
import Link from 'next/link';
import { useState } from 'react';

const CONTACT_CHANNELS = [
	{
		title: 'Tư vấn lộ trình',
		desc: 'Phù hợp khi bạn cần chọn gói học, lên nhịp ôn hoặc tìm cấu trúc đồng hành phù hợp với hiện trạng.',
		meta: 'Phản hồi ưu tiên trong giờ hành chính',
	},
	{
		title: 'Hỗ trợ kỹ thuật',
		desc: 'Dành cho lỗi đăng nhập, mất lịch sử làm bài, vấn đề tải đề hoặc hiển thị giao diện chưa ổn trên thiết bị.',
		meta: 'Ưu tiên xử lý theo mức độ gián đoạn',
	},
	{
		title: 'Kết nối học thuật',
		desc: 'Khi bạn muốn được điều phối vào phòng thảo luận phù hợp hoặc cần gợi ý buổi trao đổi theo chuyên đề.',
		meta: 'Gắn với lịch thảo luận hàng tuần',
	},
] as const;

export default function ContactPage() {
	const { student, loading, error, logout } = useAuthenticatedStudentPage(
		'Không thể tải trang liên hệ lúc này.',
	);
	const [submitted, setSubmitted] = useState(false);

	if (loading) {
		return <main className="dashboard-root">Đang tải trang liên hệ...</main>;
	}

	if (!student) {
		return (
			<main className="dashboard-root">
				<section className="dash-panel dash-error-panel">
					<h2>Không thể mở trang liên hệ</h2>
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

			<section className="contact-channel-grid">
				{CONTACT_CHANNELS.map((channel) => (
					<article key={channel.title} className="contact-channel-card">
						<p className="documents-kicker">Kênh hỗ trợ</p>
						<h2>{channel.title}</h2>
						<p>{channel.desc}</p>
						<strong>{channel.meta}</strong>
					</article>
				))}
			</section>

			<section className="dash-panel" id="contact-form">
				<div className="dash-panel-head">
					<p className="documents-kicker">Biểu mẫu liên hệ</p>
					<h2>Gửi nhu cầu trong vài dòng</h2>
				</div>

				<form
					className="contact-form-grid contact-form-grid-compact"
					onSubmit={(event) => {
						event.preventDefault();
						setSubmitted(true);
					}}
				>
					<div>
						<label className="input-label" htmlFor="contact-name">
							Họ và tên
						</label>
						<input
							id="contact-name"
							className="input-field"
							type="text"
							defaultValue={student.name ?? ''}
							placeholder="Nhập họ và tên"
						/>
					</div>

					<div>
						<label className="input-label" htmlFor="contact-email">
							Email
						</label>
						<input
							id="contact-email"
							className="input-field"
							type="email"
							defaultValue={student.email}
							placeholder="Nhập email"
						/>
					</div>

					<div className="contact-form-span">
						<label className="input-label" htmlFor="contact-message">
							Nội dung
						</label>
						<textarea
							id="contact-message"
							className="input-field input-textarea input-textarea-compact"
							placeholder="Mô tả ngắn nhu cầu của bạn."
						/>
					</div>

					<div className="contact-form-footer contact-form-footer-compact">
						<button type="submit" className="btn-primary">
							Gửi yêu cầu
						</button>
					</div>
				</form>

				{submitted ? (
					<p className="profile-success-text">
						Đã ghi nhận ở bản mô phỏng giao diện.
					</p>
				) : null}
			</section>
		</main>
	);
}
