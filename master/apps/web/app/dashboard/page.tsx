'use client';

import { formatDateTime, formatScore } from '@/components/exam/helpers';
import { GenerateOnboardingExamBody, HistoryListItem, generateOnboardingExam, getHistoryList } from '@/lib/api';
import { clearAuth, getStudent, getToken } from '@/lib/auth';
import { cacheExamDetail } from '@/lib/exam-session';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { FormEvent, useEffect, useMemo, useRef, useState } from 'react';

type Student = {
	id: string;
	name: string;
	email: string;
	grade: number;
	is_first_login: boolean;
};

const SUBJECT_OPTIONS = ['Toán'] as const;
const GRADE_OPTIONS = [10, 11, 12] as const;
const EXAM_TYPE_OPTIONS = ['Giữa kì 1', 'Cuối kì 1', 'Giữa kì 2', 'Cuối kì 2'] as const;

type HistoryGroup = {
	key: 'today' | 'recent' | 'older';
	title: string;
	items: HistoryListItem[];
};

function intentToLabel(intent: HistoryListItem['intent']) {
	return intent === 'EXAM_PRACTICE' ? 'Luyện tập' : 'Đề thi';
}

function calculateAverageScore(items: HistoryListItem[]) {
	const scoredItems = items.filter((item) => item.score !== null && item.score !== undefined);
	if (scoredItems.length === 0) {
		return 0;
	}

	const totalScore = scoredItems.reduce((sum, item) => sum + (item.score ?? 0), 0);

	return Number((totalScore / scoredItems.length).toFixed(1));
}

function getHistoryMetric(item: HistoryListItem) {
	if (item.score !== null && item.score !== undefined) {
		return `Điểm ${formatScore(item.score)}`;
	}

	return `${item.correct_count} / ${item.total_questions}`;
}

function groupHistoryItems(items: HistoryListItem[]): HistoryGroup[] {
	const startOfToday = new Date();
	startOfToday.setHours(0, 0, 0, 0);

	const startOfRecentWindow = new Date(startOfToday);
	startOfRecentWindow.setDate(startOfRecentWindow.getDate() - 7);

	const groups: Record<HistoryGroup['key'], HistoryListItem[]> = {
		today: [],
		recent: [],
		older: [],
	};

	items.forEach((item) => {
		const createdAt = new Date(item.created_at);
		if (Number.isNaN(createdAt.getTime())) {
			groups.older.push(item);
			return;
		}

		if (createdAt >= startOfToday) {
			groups.today.push(item);
			return;
		}

		if (createdAt >= startOfRecentWindow) {
			groups.recent.push(item);
			return;
		}

		groups.older.push(item);
	});

	const sections: HistoryGroup[] = [
		{ key: 'today', title: 'Hôm nay', items: groups.today },
		{ key: 'recent', title: '7 ngày gần đây', items: groups.recent },
		{ key: 'older', title: 'Cũ hơn', items: groups.older },
	];

	return sections.filter((group) => group.items.length > 0);
}

export default function DashboardPage() {
	const router = useRouter();
	const menuRef = useRef<HTMLDivElement | null>(null);
	const [student, setStudent] = useState<Student | null>(null);
	const [menuOpen, setMenuOpen] = useState(false);
	const [subject, setSubject] = useState<(typeof SUBJECT_OPTIONS)[number]>('Toán');
	const [grade, setGrade] = useState<(typeof GRADE_OPTIONS)[number]>(12);
	const [examType, setExamType] = useState<(typeof EXAM_TYPE_OPTIONS)[number]>('Giữa kì 1');
	const [onboardingError, setOnboardingError] = useState('');
	const [onboardingLoading, setOnboardingLoading] = useState(false);
	const [historyItems, setHistoryItems] = useState<HistoryListItem[]>([]);
	const [historyLoading, setHistoryLoading] = useState(true);
	const [historyError, setHistoryError] = useState('');

	useEffect(() => {
		const token = getToken();
		if (!token) {
			router.replace('/login');
			return;
		}

		setStudent(getStudent());
	}, [router]);

	useEffect(() => {
		const current = getStudent();
		if (!current) {
			return;
		}

		if (current.grade >= 10 && current.grade <= 12) {
			setGrade(current.grade as (typeof GRADE_OPTIONS)[number]);
		}
	}, []);

	useEffect(() => {
		function onDocumentClick(event: MouseEvent) {
			if (!menuRef.current) {
				return;
			}

			const target = event.target;
			if (target instanceof Node && !menuRef.current.contains(target)) {
				setMenuOpen(false);
			}
		}

		document.addEventListener('mousedown', onDocumentClick);
		return () => {
			document.removeEventListener('mousedown', onDocumentClick);
		};
	}, []);

	useEffect(() => {
		const token = getToken();
		if (!token) {
			return;
		}
		const authToken = token;

		async function loadHistory() {
			setHistoryLoading(true);
			setHistoryError('');

			try {
				const data = await getHistoryList(authToken);
				setHistoryItems(data);
			} catch {
				setHistoryError('Không thể tải lịch sử làm bài lúc này.');
			} finally {
				setHistoryLoading(false);
			}
		}

		loadHistory();
	}, []);

	function logout() {
		clearAuth();
		router.replace('/login');
	}

	async function onSubmitOnboarding(event: FormEvent<HTMLFormElement>) {
		event.preventDefault();
		setOnboardingError('');

		const token = getToken();
		if (!token) {
			router.replace('/login');
			return;
		}

		setOnboardingLoading(true);
		try {
			const exam = await generateOnboardingExam(token, {
				subject,
				grade,
				exam_type: examType,
			});
			cacheExamDetail(exam);
			router.push(`/exams/${exam.exam_id}`);
		} catch {
			setOnboardingError('Không tìm thấy đề phù hợp lúc này. Vui lòng thử lại.');
			setOnboardingLoading(false);
		}
	}

	const averageScore = useMemo(() => calculateAverageScore(historyItems), [historyItems]);
	const groupedHistoryItems = useMemo(() => groupHistoryItems(historyItems), [historyItems]);

	if (!student) {
		return null;
	}

	const showOnboarding = student.is_first_login;

	return (
		<main className="dashboard-shell">
			<header className="dash-topbar">
				<div className="dash-brand">
					<span className="dash-dot" />
					<strong>MASTER THPT</strong>
				</div>

				<nav className="dash-nav" aria-label="Main navigation">
					<Link href="/dashboard" className="dash-nav-link is-active">
						Tổng quan
					</Link>
					<Link href="/documents" className="dash-nav-link">
						Kho đề thi
					</Link>
					<Link href="/practice" className="dash-nav-link">
						Luyện tập
					</Link>
				</nav>

				<div className="dash-userbar" ref={menuRef}>
					<button
						type="button"
						className="dash-avatar-btn"
						onClick={() => setMenuOpen((prev) => !prev)}
						aria-haspopup="menu"
						aria-expanded={menuOpen}
						aria-label="Mở menu người dùng"
					>
						<span className="dash-avatar-dot" />
					</button>

					{menuOpen ? (
						<div className="dash-user-menu" role="menu">
							<p className="dash-user-menu-name">{student.name}</p>
							<p className="dash-user-menu-email">{student.email}</p>
							<button type="button" className="dash-user-menu-item" onClick={logout}>
								Đăng xuất
							</button>
						</div>
					) : null}
				</div>
			</header>

			<section className="dash-progress-layout">
				<div className="dash-history-column">
					<section className="dash-panel dash-history-panel">
						<div className="dash-panel-head">
							<h2>Lịch sử làm bài</h2>
							<p>Bấm vào từng đề để xem lại chi tiết bài làm.</p>
						</div>

						{historyLoading ? <p className="documents-message">Đang tải lịch sử...</p> : null}
						{!historyLoading && historyError ? <p className="documents-error">{historyError}</p> : null}

						{!historyLoading && !historyError ? (
							<div className="dash-history-feed">
								{groupedHistoryItems.map((group) => (
									<section key={group.key} className="dash-history-group">
										<div className="dash-history-group-head">
											<h3>{group.title}</h3>
											<span>{group.items.length}</span>
										</div>

										<div className="dash-history-list">
											{group.items.map((item) => (
												<Link key={item.history_id} href={`/history/${item.history_id}`} className="dash-history-item">
													<div className="dash-history-main">
														<div className="dash-history-topline">
															<span className="dash-badge">{intentToLabel(item.intent)}</span>
															<span className="dash-history-timestamp">{formatDateTime(item.created_at)}</span>
														</div>
														<p className="dash-history-title">
															{item.subject} - {item.exam_type}
														</p>
														<div className="dash-history-bottomline">
															<strong className="dash-history-metric">{getHistoryMetric(item)}</strong>
															<p className="dash-history-meta">
																{item.source}
																{item.grade ? ` • Lớp ${item.grade}` : ''}
																{item.year ? ` • Năm ${item.year}` : ''}
															</p>
														</div>
													</div>
													<span className="dash-history-link">Mở lại</span>
												</Link>
											))}
										</div>
									</section>
								))}

								{historyItems.length === 0 ? (
									<section className="documents-empty" aria-live="polite">
										Bạn chưa có lịch sử làm bài nào.
									</section>
								) : null}
							</div>
						) : null}
					</section>
				</div>

				<div className="dash-insights-column">
					<section className="dash-grid-cards dash-grid-cards-side">
						<article className="dash-card">
							<p className="dash-card-label">Số bài đã làm</p>
							<p className="dash-card-value">{historyItems.length}</p>
							<p className="dash-card-hint">Bao gồm cả đề thi trong kho đề và các phiên luyện tập đã hoàn tất.</p>
						</article>

						<article className="dash-card">
							<p className="dash-card-label">Điểm trung bình</p>
							<p className="dash-card-value">{formatScore(averageScore)}</p>
							<p className="dash-card-hint">Chỉ tính từ các bài làm đã có điểm số được lưu trong lịch sử.</p>
						</article>
					</section>

					<section className="dash-panel">
						<div className="dash-panel-head">
							<h2>Thống kê</h2>
							<p>Phần này sẽ hiển thị các nhóm kiến thức và xu hướng làm bài sau khi bạn thêm logic phân tích.</p>
						</div>
						<div className="dash-placeholder-box">
							Chưa có dữ liệu hiển thị.
						</div>
					</section>
				</div>
			</section>

			{showOnboarding ? (
				<div className="onboarding-overlay" role="dialog" aria-modal="true">
					<form className="onboarding-modal" onSubmit={onSubmitOnboarding}>
						<div className="onboarding-head">
							<p className="documents-kicker">Khởi tạo hồ sơ học tập</p>
							<h2>Bạn mới đăng nhập lần đầu</h2>
							<p className="text-soft">
								Chọn môn học, lớp và mốc kiến thức hiện tại để hệ thống lấy đề phù hợp trong kho đề.
							</p>
						</div>

						<div className="onboarding-form-grid">
							<div>
								<label className="input-label" htmlFor="onboarding-subject">
									Môn học
								</label>
								<select
									id="onboarding-subject"
									className="input-field"
									value={subject}
									onChange={(event) => setSubject(event.target.value as GenerateOnboardingExamBody['subject'])}
									disabled={onboardingLoading}
								>
									{SUBJECT_OPTIONS.map((option) => (
										<option key={option} value={option}>
											{option}
										</option>
									))}
								</select>
							</div>

							<div>
								<label className="input-label" htmlFor="onboarding-grade">
									Lớp
								</label>
								<select
									id="onboarding-grade"
									className="input-field"
									value={grade}
									onChange={(event) => setGrade(Number(event.target.value) as GenerateOnboardingExamBody['grade'])}
									disabled={onboardingLoading}
								>
									{GRADE_OPTIONS.map((option) => (
										<option key={option} value={option}>
											Lớp {option}
										</option>
									))}
								</select>
							</div>

							<div className="onboarding-form-full">
								<label className="input-label" htmlFor="onboarding-exam-type">
									Kiến thức hiện tại
								</label>
								<select
									id="onboarding-exam-type"
									className="input-field"
									value={examType}
									onChange={(event) => setExamType(event.target.value as GenerateOnboardingExamBody['exam_type'])}
									disabled={onboardingLoading}
								>
									{EXAM_TYPE_OPTIONS.map((option) => (
										<option key={option} value={option}>
											{option}
										</option>
									))}
								</select>
							</div>
						</div>

						<div className="onboarding-actions">
							<div />
							<button type="submit" className="btn-primary" disabled={onboardingLoading}>
								{onboardingLoading ? 'Đang tìm đề...' : 'OK'}
							</button>
						</div>

						{onboardingError ? <p className="error-text">{onboardingError}</p> : null}
					</form>
				</div>
			) : null}
		</main>
	);
}
