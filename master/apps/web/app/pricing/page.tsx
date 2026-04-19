'use client';

import { DashboardTopbar } from '@/features/dashboard/components/dashboard-topbar';
import { useAuthenticatedStudentPage } from '@/features/dashboard/lib/use-authenticated-student-page';
import Link from 'next/link';

const PLANS = [
	{
		name: 'Khởi động',
		price: '0đ',
		cadence: '/ tháng',
		description: 'Dành cho học sinh muốn bắt đầu bằng kho đề, lịch sử làm bài và nhịp ôn cá nhân thật gọn.',
		features: [
			'Truy cập kho đề và luyện tập cơ bản',
			'Theo dõi lịch sử làm bài theo từng đợt',
			'Lưu kết quả đầu vào và hồ sơ học tập',
		],
		cta: 'Dùng ngay',
		href: '/dashboard',
		featured: false,
	},
	{
		name: 'Bứt tốc',
		price: '149.000đ',
		cadence: '/ tháng',
		description: 'Phù hợp khi bạn cần thêm kỷ luật học, nhịp thảo luận nhóm và những gợi ý sát năng lực hơn.',
		features: [
			'Toàn bộ tính năng gói Khởi động',
			'Ưu tiên vào phòng thảo luận chuyên đề',
			'Checklist ôn thi theo tuần và khung mục tiêu 8+',
			'Gợi ý nhịp luyện đề bám sát tiến độ hiện tại',
		],
		cta: 'Chọn gói này',
		href: '/contact',
		featured: true,
	},
	{
		name: 'Đội nhóm đồng hành',
		price: '449.000đ',
		cadence: '/ tháng',
		description: 'Dành cho nhóm bạn hoặc phụ huynh muốn có nhịp theo dõi rõ hơn, trao đổi đều và ưu tiên hỗ trợ nhanh.',
		features: [
			'Toàn bộ tính năng gói Bứt tốc',
			'Nhóm học nhỏ có điều phối',
			'Ưu tiên phản hồi trong giờ hỗ trợ',
			'Bản tóm tắt tiến độ để phụ huynh hoặc nhóm cùng theo dõi',
		],
		cta: 'Liên hệ tư vấn',
		href: '/contact',
		featured: false,
	},
] as const;

export default function PricingPage() {
	const { student, loading, error, logout } = useAuthenticatedStudentPage(
		'Không thể tải bảng giá lúc này.',
	);

	if (loading) {
		return <main className="dashboard-root">Đang tải bảng giá...</main>;
	}

	if (!student) {
		return (
			<main className="dashboard-root">
				<section className="dash-panel dash-error-panel">
					<h2>Không thể mở bảng giá</h2>
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

			<section className="price-grid">
				{PLANS.map((plan) => (
					<article key={plan.name} className={`price-card ${plan.featured ? 'is-featured' : ''}`}>
						<div className="price-card-head">
							<span className={`dash-badge ${plan.featured ? '' : 'is-neutral'}`}>
								{plan.featured ? 'Khuyến nghị' : 'Lựa chọn'}
							</span>
							<h2>{plan.name}</h2>
							<p>{plan.description}</p>
						</div>

						<div className="price-figure">
							<strong>{plan.price}</strong>
							<span>{plan.cadence}</span>
						</div>

						<div className="price-feature-list">
							{plan.features.map((feature) => (
								<p key={feature}>{feature}</p>
							))}
						</div>

						<Link href={plan.href} className={plan.featured ? 'btn-primary' : 'btn-ghost'}>
							{plan.cta}
						</Link>
					</article>
				))}
			</section>

			<section className="dash-panel info-note-panel">
				<p className="text-soft">Gợi ý nhanh: mới bắt đầu chọn `Khởi động`, cần nhịp đều hơn chọn `Bứt tốc`, muốn học theo nhóm chọn `Đội nhóm đồng hành`.</p>
			</section>
		</main>
	);
}
