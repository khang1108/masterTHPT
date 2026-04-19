'use client';

import { Student } from '@/shared/models/student';
import { getStudentDisplayName, getStudentInitials } from '@/features/students/lib/student-profile';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';

type DashboardTopbarProps = {
	student: Student;
	onLogout: () => void;
};

type MockStudyStreak = {
	current: number;
	label: string;
};

function getMockStudyStreak(studentId: string): MockStudyStreak {
	const seed = Array.from(studentId).reduce((total, char, index) => total + char.charCodeAt(0) * (index + 3), 0);
	const current = 4 + (seed % 6);

	return {
		current,
		label: current >= 8 ? 'Nhịp học rất đều' : current >= 6 ? 'Đang giữ nhịp tốt' : 'Chuỗi đang ổn định',
	};
}

export function DashboardTopbar({ student, onLogout }: DashboardTopbarProps) {
	const pathname = usePathname();
	const menuRef = useRef<HTMLDivElement | null>(null);
	const [menuOpen, setMenuOpen] = useState(false);
	const profileStateLabel = student.profile_completed ? 'Hồ sơ đã đầy đủ' : 'Cần cập nhật hồ sơ';
	const mockStudyStreak = getMockStudyStreak(student.id);
	const navItems = [
		{ href: '/dashboard', label: 'Tổng quan' },
		{ href: '/documents', label: 'Kho đề thi' },
		{ href: '/practice', label: 'Luyện tập' },
		{ href: '/discuss', label: 'Thảo luận' },
		{ href: '/pricing', label: 'Bảng giá' },
		{ href: '/contact', label: 'Liên hệ' },
		{ href: '/profile', label: 'Hồ sơ' },
	] as const;

	function isActiveLink(href: string) {
		return pathname === href || pathname.startsWith(`${href}/`);
	}

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

	return (
		<header className="dash-topbar">
			<Link
				href="https://masterthpt.app/"
				className="dash-brand"
				target="_blank"
				rel="noreferrer"
				aria-label="Mở website masterthpt.app"
			>
				<span className="dash-dot" />
				<strong>MASTER THPT</strong>
			</Link>

			<nav className="dash-nav" aria-label="Điều hướng chính">
				{navItems.map((item) => (
					<Link
						key={item.href}
						href={item.href}
						className={`dash-nav-link ${isActiveLink(item.href) ? 'is-active' : ''}`}
					>
						{item.label}
					</Link>
				))}
			</nav>

			<div className="dash-userbar" ref={menuRef}>
				<div
					className="dash-streak-pill"
					aria-label={`Chuỗi học ${mockStudyStreak.current} ngày, ${mockStudyStreak.label.toLowerCase()}`}
					title={`Chuỗi học ${mockStudyStreak.current} ngày - ${mockStudyStreak.label}`}
				>
					<span className="dash-streak-flame" aria-hidden="true">
						<svg viewBox="0 0 24 24" focusable="false">
							<path
								d="M13.25 2.6c.2 2.05-.6 3.42-1.72 4.8-1.14 1.42-2.64 2.7-3.34 4.9-.67 2.1-.3 4.63 1.22 6.3 1.24 1.37 3.2 2.1 5.02 2.1 4.06 0 6.77-2.74 6.77-6.62 0-2.92-1.62-5.13-3.55-7.24-.9-.98-1.82-1.98-2.46-3.15-.54-.98-.91-2.01-.98-3.09-.02-.36-.45-.52-.68-.25-1.17 1.39-1.95 3.01-2.09 5.4-.88-.63-1.58-1.65-1.87-3.05-.08-.39-.61-.45-.74-.1-.28.75-.41 1.38-.4 2Z"
								fill="currentColor"
							/>
							<path
								d="M12.9 10.65c.1 1.02-.28 1.68-.82 2.37-.55.69-1.28 1.31-1.62 2.39-.33 1.02-.15 2.26.6 3.08.61.67 1.57 1.03 2.46 1.03 1.98 0 3.3-1.34 3.3-3.23 0-1.42-.79-2.5-1.73-3.53-.44-.48-.89-.97-1.2-1.54-.26-.48-.44-.98-.48-1.51-.01-.18-.22-.25-.33-.12-.57.68-.95 1.47-1.02 2.63-.43-.3-.77-.8-.91-1.49-.04-.19-.3-.22-.36-.05-.14.37-.2.67-.19.97Z"
								fill="rgba(255,255,255,0.82)"
							/>
						</svg>
					</span>
					<div className="dash-streak-copy">
						<span>Streak</span>
						<strong>
							{mockStudyStreak.current}
							<small> ngày</small>
						</strong>
					</div>
				</div>

				<button
					type="button"
					className="dash-avatar-btn"
					onClick={() => setMenuOpen((prev) => !prev)}
					aria-haspopup="menu"
					aria-expanded={menuOpen}
					aria-label="Mở menu người dùng"
				>
					<span className="dash-avatar-initials">{getStudentInitials(student)}</span>
				</button>

				{menuOpen ? (
					<div className="dash-user-menu" role="menu">
						<div className="dash-user-menu-panel">
							<div className="dash-user-menu-identity">
								<div className="dash-user-menu-avatar" aria-hidden="true">
									{getStudentInitials(student)}
								</div>
								<div className="dash-user-menu-copy">
									<p className="dash-user-menu-name">{getStudentDisplayName(student)}</p>
									<p className="dash-user-menu-email">{student.email}</p>
								</div>
							</div>
							<span className={`dash-user-menu-badge ${student.profile_completed ? '' : 'is-muted'}`}>
								{profileStateLabel}
							</span>
						</div>

						<div className="dash-user-menu-actions">
							<Link
								href="/profile"
								className="dash-user-menu-item dash-user-menu-link"
								onClick={() => setMenuOpen(false)}
							>
								<span className="dash-user-menu-item-title">
									{student.profile_completed ? 'Chỉnh sửa hồ sơ' : 'Hoàn thiện hồ sơ'}
								</span>
								<span className="dash-user-menu-item-meta">Cập nhật thông tin học tập</span>
							</Link>
							<button
								type="button"
								className="dash-user-menu-item dash-user-menu-item-danger"
								onClick={() => {
									setMenuOpen(false);
									onLogout();
								}}
							>
								<span className="dash-user-menu-item-title">Đăng xuất</span>
								<span className="dash-user-menu-item-meta">Kết thúc phiên hiện tại</span>
							</button>
						</div>
					</div>
				) : null}
			</div>
		</header>
	);
}
