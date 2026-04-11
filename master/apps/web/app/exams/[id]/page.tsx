'use client';

import { DocumentDetailResponse, ExamQuestion, getDocumentDetail, submitExam } from '@/lib/api';
import { getStudent, getToken, updateStudent } from '@/lib/auth';
import { cacheExamResult, getCachedExamDetail } from '@/lib/exam-session';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import Latex from 'react-latex-next';

type FlatQuestion = {
	id: string;
	index: number;
	sectionType: 'multiple_choice' | 'true_false' | 'short_answer';
	sectionName: string;
	question: ExamQuestion;
};

function parseOption(option: string) {
	const match = option.match(/^([A-Z])\.\s*(.*)$/);
	if (!match) {
		return {
			label: option,
			text: option,
		};
	}

	return {
		label: match[1],
		text: match[2],
	};
}

function getAlphabetLabel(index: number) {
	return String.fromCharCode(65 + index);
}

function MathText({ text }: { text: string }) {
	return (
		<span className="exam-math-text">
			<Latex>{text}</Latex>
		</span>
	);
}

export default function ExamRoomPage() {
	const router = useRouter();
	const params = useParams<{ id: string }>();
	const examId = typeof params?.id === 'string' ? params.id : '';

	const [exam, setExam] = useState<DocumentDetailResponse | null>(null);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState('');
	const [activeQuestionIndex, setActiveQuestionIndex] = useState(0);
	const [answers, setAnswers] = useState<Record<string, string>>({});
	const [isSubmitting, setIsSubmitting] = useState(false);
	const [submitError, setSubmitError] = useState('');
	const [showSubmitConfirm, setShowSubmitConfirm] = useState(false);
	const [remainingSeconds, setRemainingSeconds] = useState<number | null>(null);
	const examStartAtRef = useRef<number>(Date.now());
	const autoSubmitTriggeredRef = useRef(false);

	useEffect(() => {
		if (!examId) {
			setError('Không tìm thấy mã đề thi.');
			setLoading(false);
			return;
		}

		const token = getToken();
		if (!token) {
			router.replace('/login');
			return;
		}
		const authToken = token;

		async function loadExam() {
			setLoading(true);
			setError('');
			setSubmitError('');

			try {
				const cachedExam = getCachedExamDetail(examId);
				if (cachedExam) {
					setExam(cachedExam);
					examStartAtRef.current = Date.now();
					return;
				}

				const data = await getDocumentDetail(examId, authToken);
				setExam(data);
				examStartAtRef.current = Date.now();
			} catch {
				setError('Không tải được đề thi. Vui lòng thử lại.');
			} finally {
				setLoading(false);
			}
		}

		loadExam();
	}, [examId, router]);

	const flatQuestions = useMemo<FlatQuestion[]>(() => {
		if (!exam) {
			return [];
		}

		return exam.sections.flatMap((section) =>
			section.questions.map((question) => ({
				id: question.id,
				index: question.question_index,
				sectionType: section.type,
				sectionName: section.section_name,
				question,
			})),
		);
	}, [exam]);

	const activeQuestion = flatQuestions[activeQuestionIndex];
	const isLowTime = remainingSeconds !== null && remainingSeconds <= 10 * 60;

	const formattedRemainingTime = useMemo(() => {
		if (remainingSeconds === null) {
			return '--:--';
		}

		const safeSeconds = Math.max(remainingSeconds, 0);
		const hours = Math.floor(safeSeconds / 3600);
		const minutes = Math.floor((safeSeconds % 3600) / 60);
		const seconds = safeSeconds % 60;

		if (hours > 0) {
			return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
		}

		return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
	}, [remainingSeconds]);

	useEffect(() => {
		if (!exam) {
			setRemainingSeconds(null);
			autoSubmitTriggeredRef.current = false;
			return;
		}

		const durationInSeconds = Math.max(0, Math.floor(exam.duration_minutes * 60));
		setRemainingSeconds(durationInSeconds);
		autoSubmitTriggeredRef.current = false;

		const timer = window.setInterval(() => {
			setRemainingSeconds((prev) => {
				if (prev === null || prev <= 0) {
					return 0;
				}

				return prev - 1;
			});
		}, 1000);

		return () => {
			window.clearInterval(timer);
		};
	}, [exam]);

	function setAnswer(questionId: string, value: string) {
		setAnswers((prev) => ({
			...prev,
			[questionId]: value,
		}));
	}

	const handleSubmitExam = useCallback(async () => {
		if (!exam || isSubmitting) {
			return;
		}

		const token = getToken();
		if (!token) {
			router.replace('/login');
			return;
		}
		const authToken = token;

		const student = getStudent();
		if (!student) {
			router.replace('/login');
			return;
		}

		setShowSubmitConfirm(false);
		setSubmitError('');
		setIsSubmitting(true);

		try {
			const timeTakenSeconds = Math.max(1, Math.floor((Date.now() - examStartAtRef.current) / 1000));

			const fullExam = {
				exam_id: exam.exam_id,
				subject: exam.subject,
				exam_type: exam.exam_type,
				total_questions: exam.total_questions,
				duration_minutes: exam.duration_minutes,
				sections: exam.sections.map((section) => ({
					type: section.type,
					section_name: section.section_name,
					questions: section.questions.map((question) => ({
						id: question.id,
						question_index: question.question_index,
						type: question.type,
						content: question.content,
						options: question.options,
						statements: question.statements,
						correct_answer: question.correct_answer,
						answer: question.answer ?? question.correct_answer ?? '',
						student_answer: answers[question.id] ?? '',
						has_image: question.has_image,
						image_url: question.image_url,
					})),
				})),
			};

			const result = await submitExam(authToken, {
				student_id: student.id,
				exam_id: exam.exam_id,
				time_taken_seconds: timeTakenSeconds,
				full_exam: fullExam,
			});

			cacheExamResult(exam.exam_id, result);
			updateStudent({ is_first_login: false });
			router.push(`/exams/${exam.exam_id}/results`);
		} catch {
			setSubmitError('Nộp bài thất bại. Vui lòng thử lại sau.');
			setIsSubmitting(false);
		}
	}, [answers, exam, isSubmitting, router]);

	function openSubmitConfirm() {
		if (isSubmitting) {
			return;
		}

		setShowSubmitConfirm(true);
	}

	useEffect(() => {
		if (!exam || remainingSeconds === null || isSubmitting) {
			return;
		}

		if (remainingSeconds > 0 || autoSubmitTriggeredRef.current) {
			return;
		}

		autoSubmitTriggeredRef.current = true;
		handleSubmitExam();
	}, [exam, handleSubmitExam, isSubmitting, remainingSeconds]);

	function renderAnswerPanel(item: FlatQuestion) {
		if (item.sectionType === 'multiple_choice') {
			return (
				<div className="exam-mc-grid">
					{item.question.options?.map((option) => {
						const parsed = parseOption(option);
						const isSelected = answers[item.id] === parsed.label;

						return (
							<button
								key={`${item.id}-${parsed.label}`}
								type="button"
								className={`exam-mc-option ${isSelected ? 'is-selected' : ''}`}
								onClick={() => setAnswer(item.id, parsed.label)}
							>
								<div className="exam-mc-option-main">
									<span className="exam-mc-badge">{parsed.label}</span>
									<MathText text={parsed.text} />
								</div>
								<span className="exam-mc-tail">{parsed.label}</span>
							</button>
						);
					})}
				</div>
			);
		}

		if (item.sectionType === 'true_false') {
			const statements = item.question.statements ?? [];
			const tokens = (answers[item.id] ?? '').split(',');

			return (
				<div className="exam-tf-table">
					<div className="exam-tf-head">
						<p>PHÁT BIỂU</p>
						<p>ĐÚNG</p>
						<p>SAI</p>
					</div>

					{statements.map((statement, idx) => {
						const current = tokens[idx] ?? '';

						function updateToken(next: 'T' | 'F') {
							const clone = [...tokens];
							clone[idx] = next;
							setAnswer(item.id, clone.join(','));
						}

						return (
							<div key={`${item.id}-${idx}`} className="exam-tf-item">
								<div className="exam-tf-statement">
									<span className="exam-tf-label">{getAlphabetLabel(idx)}</span>
									<p><MathText text={statement} /></p>
								</div>

								<button
									type="button"
									className={`exam-tf-radio ${current === 'T' ? 'is-selected' : ''}`}
									onClick={() => updateToken('T')}
									aria-label={`Chọn đúng cho phát biểu ${getAlphabetLabel(idx)}`}
								/>
								<button
									type="button"
									className={`exam-tf-radio ${current === 'F' ? 'is-selected' : ''}`}
									onClick={() => updateToken('F')}
									aria-label={`Chọn sai cho phát biểu ${getAlphabetLabel(idx)}`}
								/>
							</div>
						);
					})}
				</div>
			);
		}

		return (
			<div className="exam-short-wrap">
				<input
					type="text"
					className="exam-short-input"
					placeholder=""
					value={answers[item.id] ?? ''}
					onChange={(event) => setAnswer(item.id, event.target.value)}
				/>
			</div>
		);
	}

	if (loading) {
		return <main className="exam-room">Đang tải đề thi...</main>;
	}

	if (error || !exam || !activeQuestion) {
		return (
			<main className="exam-room">
				<p className="documents-error">{error || 'Không có dữ liệu đề thi.'}</p>
				<Link href="/documents" className="btn-ghost">
					Quay lại Kho đề
				</Link>
			</main>
		);
	}

	return (
		<main className="exam-room">
			<header className="exam-header">
				<div>
					<p className="documents-kicker">Phòng thi</p>
					<h1 className="documents-title">{exam.subject} - {exam.exam_type}</h1>
					<p className="text-soft">{exam.total_questions} câu | {exam.duration_minutes} phút</p>
				</div>
				<Link href="/documents" className="btn-ghost">Thoát phòng thi</Link>
			</header>

			<section className="exam-layout">
				<article className="exam-main">
					<div className="exam-question-shell">
						<div className="exam-question-top">
							<div className="exam-question-chip">
								<span>{activeQuestion.index}</span>
								<strong>CÂU {activeQuestion.index}</strong>
							</div>
							<button type="button" className="exam-bookmark-btn">
								Đánh dấu để xem lại
							</button>
						</div>

						<div className="exam-question-content"><MathText text={activeQuestion.question.content} /></div>

						{activeQuestion.question.has_image && activeQuestion.question.image_url ? (
							<div className="exam-image-wrap">
								<img src={activeQuestion.question.image_url} alt={`Câu ${activeQuestion.index}`} className="exam-image" />
							</div>
						) : null}

						{renderAnswerPanel(activeQuestion)}
					</div>

					<div className="exam-main-actions">
						<button
							type="button"
							className="btn-ghost"
							disabled={activeQuestionIndex === 0}
							onClick={() => setActiveQuestionIndex((prev) => Math.max(prev - 1, 0))}
						>
							Câu trước
						</button>
						<button
							type="button"
							className="btn-primary"
							disabled={activeQuestionIndex >= flatQuestions.length - 1}
							onClick={() => setActiveQuestionIndex((prev) => Math.min(prev + 1, flatQuestions.length - 1))}
						>
							Câu tiếp
						</button>
					</div>
				</article>

				<aside className="exam-sidebar">
					<div className={`exam-timer ${isLowTime ? 'is-warning' : ''}`}>
						<p className="exam-timer-label">Thời gian còn lại</p>
						<p className="exam-timer-value">{formattedRemainingTime}</p>
					</div>

					<h3>Danh sách câu</h3>
					<div className="exam-index-grid">
						{flatQuestions.map((item, idx) => {
							const active = idx === activeQuestionIndex;
							const answered = Boolean(answers[item.id]);

							return (
								<button
									key={item.id}
									type="button"
									className={`exam-index-btn ${active ? 'is-active' : ''} ${answered ? 'is-answered' : ''}`}
									onClick={() => setActiveQuestionIndex(idx)}
								>
									{item.index}
								</button>
							);
						})}
					</div>

					<div className="exam-submit-wrap">
						<button
							type="button"
							className="exam-submit-btn"
							onClick={openSubmitConfirm}
							disabled={isSubmitting}
						>
							{isSubmitting ? (
								<>
									<span className="exam-submit-spinner" aria-hidden="true" />
									Đang nộp bài...
								</>
							) : (
								'Nộp bài'
							)}
						</button>
						{submitError ? <p className="documents-error exam-submit-error">{submitError}</p> : null}
					</div>
				</aside>
			</section>

			{showSubmitConfirm ? (
				<div className="exam-submit-confirm-overlay" role="dialog" aria-modal="true" aria-labelledby="submit-confirm-title">
					<div className="exam-submit-confirm-card">
						<h3 id="submit-confirm-title">Xác nhận nộp bài?</h3>
						<p>
							Sau khi nộp, hệ thống sẽ chấm điểm và chuyển sang trang kết quả.
						</p>
						<div className="exam-submit-confirm-actions">
							<button
								type="button"
								className="btn-ghost"
								onClick={() => setShowSubmitConfirm(false)}
								disabled={isSubmitting}
							>
								Hủy
							</button>
							<button
								type="button"
								className="exam-submit-confirm-btn"
								onClick={handleSubmitExam}
								disabled={isSubmitting}
							>
								{isSubmitting ? 'Đang nộp bài...' : 'Xác nhận nộp bài'}
							</button>
						</div>
					</div>
				</div>
			) : null}
		</main>
	);
}
