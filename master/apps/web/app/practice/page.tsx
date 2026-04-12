'use client';

import { generatePractice } from '@/lib/api';
import { getToken } from '@/lib/auth';
import { cacheExamDetail } from '@/lib/exam-session';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ChangeEvent, DragEvent, FormEvent, useEffect, useMemo, useRef, useState } from 'react';

const SUBJECT_OPTIONS = ['Toán Học'];
const EXAM_TYPE_OPTIONS = ['THPTQG_2025', 'THPTQG_2024', 'THPTQG_2023', 'LUYEN_TAP'];
const LOADING_TEXTS = [
	'AI đang phân tích tài liệu...',
	'Đang trích xuất câu hỏi và cấu trúc đề...',
	'Đang tạo đề thi thử từ mock service...',
];

export default function PracticePage() {
	const router = useRouter();
	const inputRef = useRef<HTMLInputElement | null>(null);
	const [token, setToken] = useState<string | null>(null);
	const [file, setFile] = useState<File | null>(null);
	const [embeddedText, setEmbeddedText] = useState('');
	const [subject, setSubject] = useState(SUBJECT_OPTIONS[0]);
	const [examType, setExamType] = useState(EXAM_TYPE_OPTIONS[0]);
	const [dragging, setDragging] = useState(false);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState('');
	const [loadingTextIndex, setLoadingTextIndex] = useState(0);

	useEffect(() => {
		const storedToken = getToken();
		if (!storedToken) {
			router.replace('/login');
			return;
		}

		setToken(storedToken);
	}, [router]);

	useEffect(() => {
		if (!loading) {
			return;
		}

		const interval = window.setInterval(() => {
			setLoadingTextIndex((prev) => (prev + 1) % LOADING_TEXTS.length);
		}, 1400);

		return () => {
			window.clearInterval(interval);
		};
	}, [loading]);

	const selectedFileLabel = useMemo(() => {
		if (!file) {
			return 'Chưa có file được chọn';
		}

		const inMb = (file.size / 1024 / 1024).toFixed(2);
		return `${file.name} (${inMb} MB)`;
	}, [file]);

	function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
		const selected = event.target.files?.[0] ?? null;
		setFile(selected);
	}

	function handleDrop(event: DragEvent<HTMLDivElement>) {
		event.preventDefault();
		setDragging(false);

		const dropped = event.dataTransfer.files?.[0] ?? null;
		if (dropped) {
			setFile(dropped);
		}
	}

	function openFileDialog() {
		inputRef.current?.click();
	}

	async function onGenerate(event: FormEvent<HTMLFormElement>) {
		event.preventDefault();

		if (!token) {
			router.replace('/login');
			return;
		}

		if (!file && embeddedText.trim().length === 0) {
			setError('Cần chọn file hoặc nhập nội dung text để tạo đề.');
			return;
		}

		setError('');
		setLoading(true);
		setLoadingTextIndex(0);

		try {
			const response = await generatePractice(token, {
				file: file ?? undefined,
				embedded_text: embeddedText,
				subject,
				exam_type: examType,
			});

			cacheExamDetail(response);
			router.push(`/exams/${response.exam_id}`);
		} catch {
			setError('Không tạo được đề thi. Vui lòng thử lại sau.');
		} finally {
			setLoading(false);
		}
	}

	return (
		<main className="practice-page">
			<header className="documents-header">
				<div>
					<p className="documents-kicker">Phòng luyện thi</p>
					<h1 className="documents-title">Tạo đề thi thử động</h1>
					<p className="text-soft">Upload file hoặc nhập text để mock AI tạo đề trong vài giây.</p>
				</div>
				<Link href="/dashboard" className="btn-ghost">
					Quay lại Dashboard
				</Link>
			</header>

			<form className="practice-grid" onSubmit={onGenerate}>
				<section
					className={`practice-dropzone ${dragging ? 'is-dragging' : ''}`}
					onDragOver={(event) => {
						event.preventDefault();
						setDragging(true);
					}}
					onDragLeave={() => setDragging(false)}
					onDrop={handleDrop}
				>
					<input
						ref={inputRef}
						type="file"
						accept=".pdf,.png,.jpg,.jpeg,.webp"
						onChange={handleFileChange}
						hidden
					/>
					<p className="practice-drop-title">Kéo thả file vào đây</p>
					<p className="practice-drop-subtitle">Hỗ trợ PDF hoặc ảnh. Bạn cũng có thể nhập text bên dưới.</p>
					<button type="button" className="btn-ghost" onClick={openFileDialog}>
						Chọn file
					</button>
					<p className="practice-file-name">{selectedFileLabel}</p>
				</section>

				<section className="practice-form-panel">
					<label className="input-label" htmlFor="embeddedText">
						Nội dung bổ sung
					</label>
					<textarea
						id="embeddedText"
						className="practice-textarea"
						placeholder="Nhập đề bài mẫu, ghi chú hoặc nội dung để AI dùng làm context..."
						value={embeddedText}
						onChange={(event) => setEmbeddedText(event.target.value)}
					/>

					<div className="split-2">
						<div>
							<label className="input-label" htmlFor="subject">
								Môn học
							</label>
							<select
								id="subject"
								className="documents-select"
								value={subject}
								onChange={(event) => setSubject(event.target.value)}
							>
								{SUBJECT_OPTIONS.map((item) => (
									<option key={item} value={item}>
										{item}
									</option>
								))}
							</select>
						</div>

						<div>
							<label className="input-label" htmlFor="examType">
								Loại đề
							</label>
							<select
								id="examType"
								className="documents-select"
								value={examType}
								onChange={(event) => setExamType(event.target.value)}
							>
								{EXAM_TYPE_OPTIONS.map((item) => (
									<option key={item} value={item}>
										{item}
									</option>
								))}
							</select>
						</div>
					</div>

					{error ? <p className="documents-error">{error}</p> : null}

					<button className="btn-primary" type="submit" disabled={loading}>
						{loading ? 'Đang tạo đề...' : 'Tạo bài thi và bắt đầu'}
					</button>
				</section>
			</form>

			{loading ? (
				<div className="practice-overlay" role="status" aria-live="polite">
					<div className="practice-overlay-card">
						<div className="practice-spinner" />
						<p>{LOADING_TEXTS[loadingTextIndex]}</p>
					</div>
				</div>
			) : null}
		</main>
	);
}
