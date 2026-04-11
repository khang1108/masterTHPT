'use client';

import { generateOnboardingExam } from '@/lib/api';
import { clearAuth, getStudent, getToken } from '@/lib/auth';
import { cacheExamDetail } from '@/lib/exam-session';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { FormEvent, useEffect, useRef, useState } from 'react';

type Student = {
	id: string;
	name: string;
	email: string;
	grade: number;
	is_first_login: boolean;
};

type ScoreRow = {
	id: string;
	label: string;
	value: string;
};

type SubjectRow = {
	id: string;
	subject: string;
	scores: ScoreRow[];
};

function buildId() {
	return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function createEmptyScore(): ScoreRow {
	return {
		id: buildId(),
		label: '',
		value: '',
	};
}

function createEmptySubject(): SubjectRow {
	return {
		id: buildId(),
		subject: '',
		scores: [createEmptyScore()],
	};
}

export default function DashboardPage() {
	const router = useRouter();
	const menuRef = useRef<HTMLDivElement | null>(null);
	const [student, setStudent] = useState<Student | null>(null);
	const [menuOpen, setMenuOpen] = useState(false);
	const [subjects, setSubjects] = useState<SubjectRow[]>([createEmptySubject()]);
	const [onboardingError, setOnboardingError] = useState('');
	const [onboardingLoading, setOnboardingLoading] = useState(false);

	useEffect(() => {
		const token = getToken();
		if (!token) {
			router.replace('/login');
			return;
		}

		setStudent(getStudent());
	}, [router]);

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

	function logout() {
		clearAuth();
		router.replace('/login');
	}

	function addSubject() {
		setSubjects((prev) => [...prev, createEmptySubject()]);
	}

	function removeSubject(subjectId: string) {
		setSubjects((prev) => {
			if (prev.length <= 1) {
				return prev;
			}

			return prev.filter((item) => item.id !== subjectId);
		});
	}

	function updateSubjectName(subjectId: string, value: string) {
		setSubjects((prev) =>
			prev.map((item) =>
				item.id === subjectId
					? {
						...item,
						subject: value,
					}
					: item,
			),
		);
	}

	function addScore(subjectId: string) {
		setSubjects((prev) =>
			prev.map((item) =>
				item.id === subjectId
					? {
						...item,
						scores: [...item.scores, createEmptyScore()],
					}
					: item,
			),
		);
	}

	function removeScore(subjectId: string, scoreId: string) {
		setSubjects((prev) =>
			prev.map((item) => {
				if (item.id !== subjectId) {
					return item;
				}

				if (item.scores.length <= 1) {
					return item;
				}

				return {
					...item,
					scores: item.scores.filter((score) => score.id !== scoreId),
				};
			}),
		);
	}

	function updateScoreField(
		subjectId: string,
		scoreId: string,
		field: 'label' | 'value',
		value: string,
	) {
		setSubjects((prev) =>
			prev.map((item) => {
				if (item.id !== subjectId) {
					return item;
				}

				return {
					...item,
					scores: item.scores.map((score) =>
						score.id === scoreId
							? {
								...score,
								[field]: value,
							}
							: score,
					),
				};
			}),
		);
	}

	async function onSubmitOnboarding(event: FormEvent<HTMLFormElement>) {
		event.preventDefault();
		setOnboardingError('');

		const token = getToken();
		if (!token) {
			router.replace('/login');
			return;
		}

		const normalized = subjects.map((subject) => ({
			subject: subject.subject.trim(),
			scores: subject.scores.map((score) => ({
				label: score.label.trim(),
				value: score.value.trim(),
			})),
		}));

		if (normalized.some((item) => item.subject.length === 0)) {
			setOnboardingError('Vui lòng nhập tên cho tất cả môn học.');
			return;
		}

		if (
			normalized.some((item) =>
				item.scores.some((score) => score.label.length === 0 || score.value.length === 0),
			)
		) {
			setOnboardingError('Vui lòng điền đầy đủ tên trường điểm và giá trị.');
			return;
		}

		setOnboardingLoading(true);
		try {
			const exam = await generateOnboardingExam(token, {
				subjects: normalized,
			});
			cacheExamDetail(exam);
			router.push(`/exams/${exam.exam_id}`);
		} catch {
			setOnboardingError('Không thể tạo đề đầu vào lúc này. Vui lòng thử lại.');
			setOnboardingLoading(false);
		}
	}

	if (!student) {
		return (
			<main style={{ minHeight: '100dvh', display: 'grid', placeItems: 'center' }}>
				<div className="practice-spinner" />
			</main>
		);
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
						Dashboard
					</Link>
					<Link href="/documents" className="dash-nav-link">
						Kho đề thi
					</Link>
					<Link href="/practice" className="dash-nav-link">
						Practice
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

			{showOnboarding ? (
				<div className="onboarding-overlay" role="dialog" aria-modal="true">
					<form className="onboarding-modal" onSubmit={onSubmitOnboarding}>
						<div className="onboarding-head">
							<p className="documents-kicker">Khởi tạo hồ sơ học tập</p>
							<h2>Bạn mới đăng nhập lần đầu</h2>
							<p className="text-soft">
								Thêm các môn học bạn muốn luyện và nhập từng loại điểm cho mỗi môn.
							</p>
						</div>

						<div className="onboarding-subject-list">
							{subjects.map((subject, index) => (
								<section key={subject.id} className="onboarding-subject-card">
									<div className="onboarding-subject-top">
										<p className="onboarding-subject-order">Môn {index + 1}</p>
										<button
											type="button"
											className="btn-ghost"
											onClick={() => removeSubject(subject.id)}
											disabled={subjects.length <= 1 || onboardingLoading}
										>
											Xóa môn
										</button>
									</div>

									<input
										type="text"
										className="input-field"
										placeholder="Ví dụ: Toán"
										value={subject.subject}
										onChange={(event) => updateSubjectName(subject.id, event.target.value)}
										disabled={onboardingLoading}
									/>

									<div className="onboarding-score-list">
										{subject.scores.map((score) => (
											<div key={score.id} className="onboarding-score-row">
												<input
													type="text"
													className="input-field"
													placeholder="Tên trường điểm (Giữa kỳ, Cuối kỳ...)"
													value={score.label}
													onChange={(event) =>
														updateScoreField(subject.id, score.id, 'label', event.target.value)
													}
													disabled={onboardingLoading}
												/>
												<input
													type="text"
													className="input-field"
													placeholder="Điểm"
													value={score.value}
													onChange={(event) =>
														updateScoreField(subject.id, score.id, 'value', event.target.value)
													}
													disabled={onboardingLoading}
												/>
												<button
													type="button"
													className="btn-ghost"
													onClick={() => removeScore(subject.id, score.id)}
													disabled={subject.scores.length <= 1 || onboardingLoading}
												>
													Xóa
												</button>
											</div>
										))}
									</div>

									<button
										type="button"
										className="btn-ghost onboarding-add-btn"
										onClick={() => addScore(subject.id)}
										disabled={onboardingLoading}
									>
										+ Thêm trường điểm cho môn này
									</button>
								</section>
							))}
						</div>

						<div className="onboarding-actions">
							<button
								type="button"
								className="btn-ghost"
								onClick={addSubject}
								disabled={onboardingLoading}
							>
								+ Thêm môn
							</button>
							<button type="submit" className="btn-primary" disabled={onboardingLoading}>
								{onboardingLoading ? 'Đang tạo đề...' : 'Bắt đầu thi ngay'}
							</button>
						</div>

						{onboardingError ? <p className="error-text">{onboardingError}</p> : null}
					</form>
				</div>
			) : null}
		</main>
	);
}
