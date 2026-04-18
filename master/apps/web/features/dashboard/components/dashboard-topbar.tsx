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

export function DashboardTopbar({ student, onLogout }: DashboardTopbarProps) {
	const pathname = usePathname();
	const menuRef = useRef<HTMLDivElement | null>(null);
	const [menuOpen, setMenuOpen] = useState(false);
	const profileStateLabel = student.profile_completed ? 'Hồ sơ đã đầy đủ' : 'Cần cập nhật hồ sơ';

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
			<div className="dash-brand">
				<span className="dash-dot" />
				<strong>MASTER THPT</strong>
			</div>

			<nav className="dash-nav" aria-label="Điều hướng chính">
				<Link href="/dashboard" className={`dash-nav-link ${pathname === '/dashboard' ? 'is-active' : ''}`}>
					Tổng quan
				</Link>
				<Link href="/documents" className={`dash-nav-link ${pathname === '/documents' ? 'is-active' : ''}`}>
					Kho đề thi
				</Link>
				<Link href="/practice" className={`dash-nav-link ${pathname === '/practice' ? 'is-active' : ''}`}>
					Luyện tập
				</Link>
				<Link href="/profile" className={`dash-nav-link ${pathname === '/profile' ? 'is-active' : ''}`}>
					Hồ sơ
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
