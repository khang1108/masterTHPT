'use client';

import { DocumentItem, getDocuments } from '@/lib/api';
import { getToken } from '@/lib/auth';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';

function normalize(value: string) {
	return value.toLowerCase().trim();
}

export default function DocumentsPage() {
	const router = useRouter();
	const [documents, setDocuments] = useState<DocumentItem[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState('');
	const [searchInput, setSearchInput] = useState('');
	const [searchValue, setSearchValue] = useState('');
	const [subjectFilter, setSubjectFilter] = useState('all');
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

	const filteredDocuments = useMemo(() => {
		const keyword = normalize(searchValue);

		return documents.filter((item) => {
			const matchedKeyword =
				keyword.length === 0 ||
				normalize(item.title).includes(keyword) ||
				normalize(item.subject).includes(keyword) ||
				normalize(item.exam_type).includes(keyword);

			const matchedSubject =
				subjectFilter === 'all' || item.subject === subjectFilter;

			const matchedYear = yearFilter === 'all' || String(item.year) === yearFilter;

			return matchedKeyword && matchedSubject && matchedYear;
		});
	}, [documents, searchValue, subjectFilter, yearFilter]);

	return (
		<main className="documents-page">
			<header className="documents-header">
				<div>
					<p className="documents-kicker">Kho đề thi</p>
					<h1 className="documents-title">Danh sách đề thi</h1>
					<p className="text-soft">Tìm đề theo môn, năm và từ khóa.</p>
				</div>
				<Link href="/dashboard" className="btn-ghost">
					Quay lại Dashboard
				</Link>
			</header>

			<section className="documents-toolbar" aria-label="Documents filters">
				<input
					type="text"
					className="input-field"
					placeholder="Tìm theo tên đề, môn học, exam type..."
					value={searchInput}
					onChange={(event) => setSearchInput(event.target.value)}
				/>

				<select
					className="documents-select"
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
					className="documents-select"
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
								<p className="documents-card-type">{item.type}</p>
								<h2 className="documents-card-title">{item.title}</h2>
								<p className="documents-card-meta">{item.subject}</p>
								<div className="documents-tags">
									<span className="documents-tag">Năm {item.year}</span>
									<span className="documents-tag">{item.exam_type}</span>
									<span className="documents-tag">ID {item.id}</span>
								</div>
								<div className="documents-card-actions">
									<Link href={`/exams/${item.id}`} className="btn-primary documents-start-btn">
										Làm bài
									</Link>
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
