'use client';

import { DashboardTopbar } from '@/features/dashboard/components/dashboard-topbar';
import { DocumentItem, getDocuments } from '@/shared/api/client';
import { clearAuth, getStudent, getToken } from '@/shared/auth/storage';
import { Student } from '@/shared/models/student';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';

function normalize(value: string) {
	return value.toLowerCase().trim();
}

function formatDocumentPrimaryMetric(item: DocumentItem) {
	const parts: string[] = [];

	if (typeof item.total_questions === 'number') {
		parts.push(`${item.total_questions} câu`);
	}

	if (typeof item.duration === 'number') {
		parts.push(`${item.duration} phút`);
	}

	return parts.join(' • ') || 'Thông tin đề đang được cập nhật';
}

function formatDocumentSecondaryMeta(item: DocumentItem) {
	const parts = [item.source ?? 'Nguồn chưa cập nhật'];

	if (typeof item.year === 'number') {
		parts.push(`Năm ${item.year}`);
	}

	return parts.join(' • ');
}

export default function DocumentsPage() {
	const router = useRouter();
	const [currentStudent, setCurrentStudent] = useState<Student | null>(null);
	const [documents, setDocuments] = useState<DocumentItem[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState('');
	const [searchInput, setSearchInput] = useState('');
	const [searchValue, setSearchValue] = useState('');
	const [subjectFilter, setSubjectFilter] = useState('all');
	const [gradeFilter, setGradeFilter] = useState('all');
	const [yearFilter, setYearFilter] = useState('all');

	useEffect(() => {
		const handle = window.setTimeout(() => {
			setSearchValue(searchInput);
		}, 300);

		return () => {
			window.clearTimeout(handle);
		};
	}, [searchInput]);

	useEffect(() => {
		const token = getToken();
		if (!token) {
			router.replace('/login');
			return;
		}

		setCurrentStudent(getStudent());
		const authToken = token;

		async function loadDocuments() {
			setLoading(true);
			setError('');

			try {
				const data = await getDocuments(authToken);
				setDocuments(data);
			} catch {
				setError('Không thể tải kho đề. Vui lòng thử lại.');
			} finally {
				setLoading(false);
			}
		}

		loadDocuments();
	}, [router]);

	const subjects = useMemo(() => {
		return ['all', ...new Set(documents.map((item) => item.subject))];
	}, [documents]);

	const years = useMemo(() => {
		const mapped = documents.map((item) => String(item.year));
		return ['all', ...new Set(mapped)];
	}, [documents]);

	const grades = useMemo(() => {
		const mapped = documents.map((item) => String(item.grade));
		return ['all', ...Array.from(new Set(mapped)).sort((a, b) => Number(a) - Number(b))];
	}, [documents]);

	const filteredDocuments = useMemo(() => {
		const keyword = normalize(searchValue);

		return documents.filter((item) => {
			const source = item.source ?? '';
			const title = item.title ?? '';
			const matchedKeyword =
				keyword.length === 0 ||
				normalize(title).includes(keyword) ||
				normalize(item.subject).includes(keyword) ||
				normalize(item.exam_type).includes(keyword) ||
				normalize(source).includes(keyword);

			const matchedSubject =
				subjectFilter === 'all' || item.subject === subjectFilter;

			const matchedGrade = gradeFilter === 'all' || String(item.grade) === gradeFilter;

			const matchedYear = yearFilter === 'all' || String(item.year) === yearFilter;

			return matchedKeyword && matchedSubject && matchedGrade && matchedYear;
		});
	}, [documents, gradeFilter, searchValue, subjectFilter, yearFilter]);

	function logout() {
		clearAuth();
		router.replace('/login');
	}

	return (
		<main className="dashboard-shell documents-page">
			{currentStudent ? <DashboardTopbar student={currentStudent} onLogout={logout} /> : null}

			<section className="documents-toolbar" aria-label="Documents filters">
				<input
					type="text"
					className="input-field documents-search-input"
					placeholder="Tìm theo tên đề, môn học, exam type..."
					value={searchInput}
					onChange={(event) => setSearchInput(event.target.value)}
				/>

				<select
					className="documents-select documents-select-subject"
					value={subjectFilter}
					onChange={(event) => setSubjectFilter(event.target.value)}
				>
					{subjects.map((subject) => (
						<option key={subject} value={subject}>
							{subject === 'all' ? 'Tất cả môn học' : subject}
						</option>
					))}
				</select>

				<select
					className="documents-select documents-select-grade"
					value={gradeFilter}
					onChange={(event) => setGradeFilter(event.target.value)}
				>
					{grades.map((grade) => (
						<option key={grade} value={grade}>
							{grade === 'all' ? 'Tất cả lớp' : `Lớp ${grade}`}
						</option>
					))}
				</select>

				<select
					className="documents-select documents-select-year"
					value={yearFilter}
					onChange={(event) => setYearFilter(event.target.value)}
				>
					{years.map((year) => (
						<option key={year} value={year}>
							{year === 'all' ? 'Tất cả năm' : year}
						</option>
					))}
				</select>
			</section>

			{loading ? <p className="documents-message">Đang tải kho đề...</p> : null}
			{!loading && error ? <p className="documents-error">{error}</p> : null}

			{!loading && !error ? (
				<>
					<p className="documents-count">
						Hiển thị {filteredDocuments.length} / {documents.length} đề thi
					</p>
					<section className="documents-grid">
						{filteredDocuments.map((item) => (
							<article key={item.id} className="documents-card">
								<div className="documents-card-top">
									<p className="documents-card-type">{item.exam_type}</p>
									<h2 className="documents-card-title">
										{item.subject} - {item.exam_type}
									</h2>
									<p className="documents-card-stat">{formatDocumentPrimaryMetric(item)}</p>
									<p className="documents-card-meta">{formatDocumentSecondaryMeta(item)}</p>
								</div>
								<div className="documents-card-bottom">
									<div className="documents-tags">
										<span className="documents-tag">Lớp {item.grade}</span>
									</div>
									<div className="documents-card-actions">
										<Link href={`/exams/${item.id}`} className="btn-primary documents-start-btn">
											Làm bài
										</Link>
									</div>
								</div>
							</article>
						))}
					</section>

					{filteredDocuments.length === 0 ? (
						<div className="documents-empty">
							Không tìm thấy đề phù hợp với bộ lọc hiện tại.
						</div>
					) : null}
				</>
			) : null}
		</main>
	);
}
