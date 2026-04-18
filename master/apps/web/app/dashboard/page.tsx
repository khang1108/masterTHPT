'use client';

import { DashboardPageSkeleton } from '@/features/dashboard/components/loading-skeletons';
import { DashboardTopbar } from '@/features/dashboard/components/dashboard-topbar';
import { StudentProfileFields } from '@/features/students/components/student-profile-fields';
import { formatDateTime, formatScore } from '@/features/exams/lib/helpers';
import {
	GenerateOnboardingExamBody,
	HistoryListItem,
	generateOnboardingExam,
	getCurrentStudent,
	getHistoryList,
	updateCurrentStudent,
} from '@/shared/api/client';
import { getApiErrorMessage, isInvalidSessionError } from '@/shared/api/error-message';
import { clearAuth, getToken, saveStudent } from '@/shared/auth/storage';
import { cacheExamDetail } from '@/features/exams/lib/exam-runtime-store';
import { Student } from '@/shared/models/student';
import {
	createStudentProfileDraft,
	StudentProfileFormValue,
} from '@/features/students/lib/student-profile';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { FormEvent, useEffect, useMemo, useState } from 'react';

const SUBJECT_OPTIONS = ['Toán'] as const;
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
	const [student, setStudent] = useState<Student | null>(null);
	const [pageLoading, setPageLoading] = useState(true);
	const [studentError, setStudentError] = useState('');
	const [profileDraft, setProfileDraft] = useState<StudentProfileFormValue>(createStudentProfileDraft());
	const [profileSaving, setProfileSaving] = useState(false);
	const [profileError, setProfileError] = useState('');
	const [subject, setSubject] = useState<(typeof SUBJECT_OPTIONS)[number]>('Toán');
	const [grade, setGrade] = useState<GenerateOnboardingExamBody['grade']>(12);
	const [examType, setExamType] = useState<(typeof EXAM_TYPE_OPTIONS)[number]>('Giữa kì 1');
	const [onboardingError, setOnboardingError] = useState('');
	const [onboardingLoading, setOnboardingLoading] = useState(false);
	const [historyItems, setHistoryItems] = useState<HistoryListItem[]>([]);
	const [historyLoading, setHistoryLoading] = useState(true);
	const [historyError, setHistoryError] = useState('');
	const [collapsedHistoryGroups, setCollapsedHistoryGroups] = useState<Record<HistoryGroup['key'], boolean>>({
		today: false,
		recent: false,
		older: false,
	});

	useEffect(() => {
		const token = getToken();
		if (!token) {
			router.replace('/login');
			return;
		}
		const authToken = token;

		let cancelled = false;

		async function loadDashboard() {
			setPageLoading(true);
			setStudentError('');
			setHistoryLoading(true);
			setHistoryError('');

			const [studentResult, historyResult] = await Promise.allSettled([
				getCurrentStudent(authToken),
				getHistoryList(authToken),
			]);

			if (cancelled) {
				return;
			}

			if (studentResult.status === 'rejected') {
				if (isInvalidSessionError(studentResult.reason)) {
					clearAuth();
					router.replace('/login');
					return;
				}

				setStudentError(getApiErrorMessage(studentResult.reason, 'Không thể tải hồ sơ học sinh.'));
				setPageLoading(false);
				setHistoryLoading(false);
				return;
			}

			setStudent(studentResult.value);
			setProfileDraft(createStudentProfileDraft(studentResult.value));
			saveStudent(studentResult.value);
			setPageLoading(false);

			if (historyResult.status === 'fulfilled') {
				setHistoryItems(historyResult.value);
				setHistoryError('');
			} else {
				setHistoryError('Không thể tải lịch sử làm bài lúc này.');
			}

			setHistoryLoading(false);
		}

		void loadDashboard();

		return () => {
			cancelled = true;
		};
	}, [router]);

	useEffect(() => {
		if (!student) {
			return;
		}

		if (student.grade && student.grade >= 10 && student.grade <= 12) {
			setGrade(student.grade as GenerateOnboardingExamBody['grade']);
		}
	}, [student]);

	function logout() {
		clearAuth();
		router.replace('/login');
	}

	function toggleHistoryGroup(groupKey: HistoryGroup['key']) {
		setCollapsedHistoryGroups((current) => ({
			...current,
			[groupKey]: !current[groupKey],
		}));
	}

	async function onSubmitProfile(event: FormEvent<HTMLFormElement>) {
		event.preventDefault();
		setProfileError('');

		const token = getToken();
		if (!token) {
			router.replace('/login');
			return;
		}

		setProfileSaving(true);
		try {
			const updatedStudent = await updateCurrentStudent(token, profileDraft);
			setStudent(updatedStudent);
			setProfileDraft(createStudentProfileDraft(updatedStudent));
			saveStudent(updatedStudent);
		} catch (error: unknown) {
			setProfileError(getApiErrorMessage(error, 'Không thể lưu thông tin cá nhân.'));
		} finally {
			setProfileSaving(false);
		}
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
		} catch (error: unknown) {
			setOnboardingError(getApiErrorMessage(error, 'Không tìm thấy đề phù hợp lúc này. Vui lòng thử lại.'));
			setOnboardingLoading(false);
		}
	}

	const averageScore = useMemo(() => calculateAverageScore(historyItems), [historyItems]);
	const groupedHistoryItems = useMemo(() => groupHistoryItems(historyItems), [historyItems]);

	useEffect(() => {
		setCollapsedHistoryGroups((current) => ({
			today: current.today ?? false,
			recent: current.recent ?? false,
			older: current.older ?? false,
		}));
	}, [groupedHistoryItems]);

	if (pageLoading) {
		return <DashboardPageSkeleton />;
	}

	if (!student) {
		return (
			<main className="dashboard-root">
				<section className="dash-panel dash-error-panel">
					<h2>Không thể mở dashboard</h2>
					<p className="text-soft">{studentError || 'Thiếu thông tin đăng nhập hoặc hồ sơ học sinh.'}</p>
					<div className="dash-inline-actions">
						<Link href="/login" className="btn-primary">
							Về trang đăng nhập
						</Link>
					</div>
				</section>
			</main>
		);
	}

	const showProfileModal = !student.profile_completed;
	const showExamModal = student.profile_completed && student.is_first_login;

	return (
			<main className="dashboard-shell">
				<DashboardTopbar student={student} onLogout={logout} />

				<section className="dash-progress-layout">
					<div className="dash-history-column">
						<section className="dash-panel dash-history-panel">
							<div className="dash-panel-head">
								<h2>Lịch sử làm bài</h2>
								<p>Chọn từng đề để xem lại chi tiết bài làm.</p>
						</div>

						{historyLoading ? (
							<div className="dash-history-feed dash-history-feed-skeleton" aria-hidden="true">
								{Array.from({ length: 3 }).map((_, index) => (
									<div key={index} className="dash-history-item dash-history-item-skeleton">
										<div className="dash-history-main">
											<div className="dash-history-topline">
												<span className="ui-skeleton dash-skeleton-badge" />
												<span className="ui-skeleton dash-skeleton-time" />
											</div>
											<span className="ui-skeleton dash-skeleton-title" />
											<div className="dash-history-bottomline">
												<span className="ui-skeleton dash-skeleton-metric" />
												<span className="ui-skeleton dash-skeleton-meta" />
											</div>
										</div>
										<span className="ui-skeleton dash-skeleton-link" />
									</div>
								))}
							</div>
						) : null}
						{!historyLoading && historyError ? <p className="documents-error">{historyError}</p> : null}

						{!historyLoading && !historyError ? (
							<div className="dash-history-feed">
								{groupedHistoryItems.map((group) => (
									<section key={group.key} className="dash-history-group">
										<div className="dash-history-group-head">
											<button
												type="button"
												className={`dash-history-group-toggle ${collapsedHistoryGroups[group.key] ? 'is-collapsed' : ''}`}
												onClick={() => toggleHistoryGroup(group.key)}
												aria-expanded={!collapsedHistoryGroups[group.key]}
												aria-controls={`history-group-${group.key}`}
											>
												<span className="dash-history-group-toggle-copy">
													<h3>{group.title}</h3>
													<span className="dash-history-group-count">{group.items.length}</span>
												</span>
												<span className="dash-history-group-toggle-icon" aria-hidden="true">
													<svg viewBox="0 0 16 16" focusable="false">
														<path d="M4.47 6.22a.75.75 0 0 1 1.06 0L8 8.69l2.47-2.47a.75.75 0 1 1 1.06 1.06l-3 3a.75.75 0 0 1-1.06 0l-3-3a.75.75 0 0 1 0-1.06Z" fill="currentColor" />
													</svg>
												</span>
											</button>
										</div>

										{!collapsedHistoryGroups[group.key] ? (
											<div id={`history-group-${group.key}`} className="dash-history-list">
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
										) : null}
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
					</div>
				</section>

			{showProfileModal ? (
				<div className="onboarding-overlay" role="dialog" aria-modal="true" aria-labelledby="profile-onboarding-title">
					<form className="onboarding-modal onboarding-modal-profile" onSubmit={onSubmitProfile}>
						<div className="onboarding-head">
							<p className="documents-kicker">Điền thông tin cá nhân</p>
							<h2 id="profile-onboarding-title">Hoàn thiện hồ sơ học tập</h2>
							<p className="text-soft">
								Hãy nhập họ tên, lớp, trường và mục tiêu học tập. Sau bước này
								hệ thống sẽ mở form chọn bài đầu vào mà bạn đã có sẵn.
							</p>
						</div>

						<StudentProfileFields
							idPrefix="onboarding-profile"
							value={profileDraft}
							onChange={setProfileDraft}
							disabled={profileSaving}
						/>

						<div className="onboarding-actions">
							<p className="onboarding-side-copy">
								Thông tin này sẽ được lưu lại và bạn có thể chỉnh sửa ở trang hồ sơ.
							</p>
							<button type="submit" className="btn-primary" disabled={profileSaving}>
								{profileSaving ? 'Đang lưu...' : 'Lưu và tiếp tục'}
							</button>
						</div>

						{profileError ? <p className="error-text">{profileError}</p> : null}
					</form>
				</div>
			) : null}

			{showExamModal ? (
				<div className="onboarding-overlay" role="dialog" aria-modal="true" aria-labelledby="exam-onboarding-title">
					<form className="onboarding-modal" onSubmit={onSubmitOnboarding}>
						<div className="onboarding-head">
							<p className="documents-kicker">Bài đầu vào</p>
							<h2 id="exam-onboarding-title">Chọn đề khởi tạo năng lực</h2>
							<p className="text-soft">
								Chọn môn học, học kì và lớp hiện tại. Hệ thống sẽ lấy một đề phù hợp trong kho đề để bạn bắt đầu.
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
									<option value={10}>Lớp 10</option>
									<option value={11}>Lớp 11</option>
									<option value={12}>Lớp 12</option>
								</select>
							</div>

							<div className="onboarding-form-full">
								<label className="input-label" htmlFor="onboarding-exam-type">
									Học kì
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
							<p className="onboarding-side-copy">
								Bạn chỉ cần làm bài này một lần. Kết quả sẽ được dùng để khởi tạo lộ trình ôn luyện.
							</p>
							<button type="submit" className="btn-primary" disabled={onboardingLoading}>
								{onboardingLoading ? 'Đang tìm đề...' : 'Bắt đầu làm bài'}
							</button>
						</div>

						{onboardingError ? <p className="error-text">{onboardingError}</p> : null}
					</form>
				</div>
			) : null}
		</main>
	);
}
