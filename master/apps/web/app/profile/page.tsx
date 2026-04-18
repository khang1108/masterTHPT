'use client';

import { DashboardTopbar } from '@/features/dashboard/components/dashboard-topbar';
import { StudentProfileFields } from '@/features/students/components/student-profile-fields';
import { getCurrentStudent, updateCurrentStudent } from '@/shared/api/client';
import { getApiErrorMessage, isInvalidSessionError } from '@/shared/api/error-message';
import { clearAuth, getToken, saveStudent } from '@/shared/auth/storage';
import { Student } from '@/shared/models/student';
import { createStudentProfileDraft, StudentProfileFormValue } from '@/features/students/lib/student-profile';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { FormEvent, useEffect, useState } from 'react';

export default function ProfilePage() {
	const router = useRouter();
	const [student, setStudent] = useState<Student | null>(null);
	const [draft, setDraft] = useState<StudentProfileFormValue>(createStudentProfileDraft());
	const [loading, setLoading] = useState(true);
	const [saving, setSaving] = useState(false);
	const [error, setError] = useState('');
	const [successMessage, setSuccessMessage] = useState('');

	useEffect(() => {
		const token = getToken();
		if (!token) {
			router.replace('/login');
			return;
		}
		const authToken = token;

		let cancelled = false;

		async function loadStudent() {
			setLoading(true);
			setError('');

			try {
				const currentStudent = await getCurrentStudent(authToken);
				if (cancelled) {
					return;
				}

				setStudent(currentStudent);
				setDraft(createStudentProfileDraft(currentStudent));
				saveStudent(currentStudent);
			} catch (requestError: unknown) {
				if (isInvalidSessionError(requestError)) {
					clearAuth();
					router.replace('/login');
					return;
				}

				setError(getApiErrorMessage(requestError, 'Không thể tải hồ sơ lúc này.'));
			} finally {
				if (!cancelled) {
					setLoading(false);
				}
			}
		}

		void loadStudent();

		return () => {
			cancelled = true;
		};
	}, [router]);

	function logout() {
		clearAuth();
		router.replace('/login');
	}

	async function onSubmit(event: FormEvent<HTMLFormElement>) {
		event.preventDefault();
		setError('');
		setSuccessMessage('');

		const token = getToken();
		if (!token) {
			router.replace('/login');
			return;
		}

		setSaving(true);
		try {
			const updatedStudent = await updateCurrentStudent(token, draft);
			setStudent(updatedStudent);
			setDraft(createStudentProfileDraft(updatedStudent));
			saveStudent(updatedStudent);
			setSuccessMessage('Hồ sơ đã được cập nhật.');
		} catch (requestError: unknown) {
			setError(getApiErrorMessage(requestError, 'Không thể lưu hồ sơ lúc này.'));
		} finally {
			setSaving(false);
		}
	}

	if (loading) {
		return <main className="dashboard-root">Đang tải hồ sơ...</main>;
	}

	if (!student) {
		return (
			<main className="dashboard-root">
				<section className="dash-panel dash-error-panel">
					<h2>Không thể tải hồ sơ</h2>
					<p className="text-soft">{error || 'Thiếu dữ liệu hồ sơ học sinh.'}</p>
					<div className="dash-inline-actions">
						<Link href="/dashboard" className="btn-primary">
							Về dashboard
						</Link>
					</div>
				</section>
			</main>
		);
	}

	return (
		<main className="dashboard-shell">
			<DashboardTopbar student={student} onLogout={logout} />

			<section className="profile-layout">
				<section className="dash-panel profile-main-panel">
					<div className="dash-panel-head">
						<p className="documents-kicker">Hồ sơ học sinh</p>
						<h2>Chỉnh sửa thông tin cá nhân</h2>
					</div>

					<form className="profile-form" onSubmit={onSubmit}>
						<StudentProfileFields
							idPrefix="profile-page"
							value={draft}
							onChange={setDraft}
							disabled={saving}
						/>

						<div className="profile-form-footer">
							<div>
								{error ? <p className="error-text">{error}</p> : null}
								{successMessage ? <p className="profile-success-text">{successMessage}</p> : null}
							</div>
							<button type="submit" className="btn-primary" disabled={saving}>
								{saving ? 'Đang lưu...' : 'Lưu thay đổi'}
							</button>
						</div>
					</form>
				</section>

				<aside className="profile-side-column">
					<section className="dash-panel profile-side-panel">
						<div className="dash-panel-head">
							<h2>Trạng thái</h2>
						</div>

						<div className="profile-meta-list">
							<div>
								<span>Email</span>
								<strong>{student.email}</strong>
							</div>
							<div>
								<span>Hồ sơ</span>
								<strong>{student.profile_completed ? 'Đã hoàn thiện' : 'Cần bổ sung'}</strong>
							</div>
							<div>
								<span>Bài đầu vào</span>
								<strong>{student.is_first_login ? 'Chưa làm' : 'Đã hoàn tất'}</strong>
							</div>
						</div>

						{student.is_first_login ? (
							<div className="profile-note-card">
								<p className="dash-card-label">Bước tiếp theo</p>
								<Link href="/dashboard" className="btn-ghost">
									Về dashboard
								</Link>
							</div>
						) : null}
					</section>
				</aside>
			</section>
		</main>
	);
}
