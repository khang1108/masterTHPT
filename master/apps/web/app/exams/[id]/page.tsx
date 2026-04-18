'use client';

import { EditableAnswerPanel } from '@/features/exams/components/editable-answer-panel';
import { QuestionFeedbackPanels } from '@/features/exams/components/feedback-panels';
import { MathText } from '@/features/exams/components/math-text';
import { ExamQuestionHeader } from '@/features/exams/components/question-header';
import { FlatQuestion, flattenExamSections } from '@/features/exams/lib/types';
import {
	DocumentDetailResponse,
	PracticeQuestionCheckResponse,
	askHint,
	checkPracticeQuestion,
	createHistory,
	getDocumentDetail,
	reviewMistake,
	submitExam,
} from '@/shared/api/client';
import { getApiErrorMessage } from '@/shared/api/error-message';
import { getStudent, getToken, updateStudent } from '@/shared/auth/storage';
import {
	cacheExamDetail,
	cacheExamQuestionTimings,
	cacheExamResult,
	clearCachedExamQuestionTimings,
	clearCachedExamResult,
	clearExamRuntimeCache,
	getCachedExamDetail,
} from '@/features/exams/lib/exam-runtime-store';
import Link from 'next/link';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

function hasAnswerValue(value?: string) {
	if (!value) {
		return false;
	}

	return value.split(',').some((token) => token.trim().length > 0);
}

export default function ExamRoomPage() {
	const router = useRouter();
	const params = useParams<{ id: string }>();
	const searchParams = useSearchParams();
	const examId = typeof params?.id === 'string' ? params.id : '';
	const isPracticeMode = searchParams.get('intent') === 'practice';

	const [exam, setExam] = useState<DocumentDetailResponse | null>(null);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState('');
	const [activeQuestionIndex, setActiveQuestionIndex] = useState(0);
	const [answers, setAnswers] = useState<Record<string, string>>({});
	const [isSubmitting, setIsSubmitting] = useState(false);
	const [submitError, setSubmitError] = useState('');
	const [checkError, setCheckError] = useState('');
	const [showSubmitConfirm, setShowSubmitConfirm] = useState(false);
	const [showExitConfirm, setShowExitConfirm] = useState(false);
	const [remainingSeconds, setRemainingSeconds] = useState<number | null>(null);
	const [checkingQuestionId, setCheckingQuestionId] = useState<string | null>(null);
	const [isCompletingPractice, setIsCompletingPractice] = useState(false);
	const [checkedResults, setCheckedResults] = useState<Record<string, PracticeQuestionCheckResponse>>({});
	const [hintFeedbacks, setHintFeedbacks] = useState<Record<string, string>>({});
	const [loadingHintQuestionId, setLoadingHintQuestionId] = useState<string | null>(null);
	const [hintError, setHintError] = useState('');
	const [reviewFeedbacks, setReviewFeedbacks] = useState<Record<string, string>>({});
	const [loadingReviewQuestionId, setLoadingReviewQuestionId] = useState<string | null>(null);
	const [reviewError, setReviewError] = useState('');
	const [practiceCompleteError, setPracticeCompleteError] = useState('');
	const examStartAtRef = useRef<number>(Date.now());
	const autoSubmitTriggeredRef = useRef(false);
	const questionTimeMsByIdRef = useRef<Record<string, number>>({});
	const activeQuestionIdRef = useRef<string | null>(null);
	const activeQuestionStartedAtRef = useRef<number | null>(null);

	function commitCurrentQuestionTime() {
		if (!activeQuestionIdRef.current || activeQuestionStartedAtRef.current === null) {
			return;
		}

		const elapsedMs = Math.max(0, Date.now() - activeQuestionStartedAtRef.current);
		questionTimeMsByIdRef.current[activeQuestionIdRef.current] =
			(questionTimeMsByIdRef.current[activeQuestionIdRef.current] ?? 0) + elapsedMs;
		activeQuestionStartedAtRef.current = null;
	}

	function resumeCurrentQuestionTime() {
		if (
			!activeQuestionIdRef.current ||
			activeQuestionStartedAtRef.current !== null ||
			document.visibilityState === 'hidden'
		) {
			return;
		}

		activeQuestionStartedAtRef.current = Date.now();
	}

	function getQuestionTimeSecondsMap() {
		return Object.fromEntries(
			Object.entries(questionTimeMsByIdRef.current).map(([questionId, elapsedMs]) => [
				questionId,
				Math.max(0, Math.round(elapsedMs / 1000)),
			]),
		);
	}

	function buildStudentAnswerRecords() {
		const questionTimeSecondsById = getQuestionTimeSecondsMap();

		return exam?.sections.flatMap((section) =>
			section.questions.map((question) => ({
				question_id: question.question_id,
				student_answer: answers[question.question_id] ?? '',
				time_spent_seconds: questionTimeSecondsById[question.question_id] ?? 0,
			})),
		) ?? [];
	}

	const flatQuestions = useMemo<FlatQuestion[]>(() => {
		if (!exam) {
			return [];
		}

		return flattenExamSections(exam.sections);
	}, [exam]);

	const activeQuestion = flatQuestions[activeQuestionIndex];

	const handlePracticeComplete = useCallback(async () => {
		const token = getToken();
		if (!token || !examId) {
			if (examId) {
				clearExamRuntimeCache(examId);
			}

			router.push('/practice');
			return;
		}

		commitCurrentQuestionTime();
		const studentAnswers = buildStudentAnswerRecords();
		setPracticeCompleteError('');
		setIsCompletingPractice(true);

		try {
			await createHistory(token, {
				intent: 'EXAM_PRACTICE',
				exam_id: examId,
				student_ans: studentAnswers,
				correct_count: Object.values(checkedResults).filter((item) => item.is_correct).length,
			});
			clearExamRuntimeCache(examId);
			router.push('/practice');
		} catch (error) {
			setPracticeCompleteError(getApiErrorMessage(error, 'Không thể hoàn tất lượt luyện tập lúc này. Vui lòng thử lại.'));
			setIsCompletingPractice(false);
		}
	}, [answers, checkedResults, exam, examId, router]);

	const handlePracticeDiscard = useCallback(() => {
		clearExamRuntimeCache(examId);
		router.push('/practice');
	}, [examId, router]);

	useEffect(() => {
		if (!examId) {
			setError('Không tìm thấy mã đề thi.');
			setLoading(false);
			return;
		}

		clearCachedExamResult(examId);
		clearCachedExamQuestionTimings(examId);

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
			setCheckError('');
			setPracticeCompleteError('');

			try {
				const cachedExam = getCachedExamDetail(examId);
				if (cachedExam) {
					setExam(cachedExam);
					examStartAtRef.current = Date.now();
					return;
				}

				const data = await getDocumentDetail(examId, authToken);
				cacheExamDetail(data);
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

	useEffect(() => {
		if (!activeQuestion?.question_id) {
			commitCurrentQuestionTime();
			activeQuestionIdRef.current = null;
			return;
		}

		if (activeQuestionIdRef.current !== activeQuestion.question_id) {
			commitCurrentQuestionTime();
			activeQuestionIdRef.current = activeQuestion.question_id;
		}

		resumeCurrentQuestionTime();
	}, [activeQuestion?.question_id]);

	useEffect(() => {
		function handleVisibilityChange() {
			if (document.visibilityState === 'hidden') {
				commitCurrentQuestionTime();
				return;
			}

			resumeCurrentQuestionTime();
		}

		function handlePageHide() {
			commitCurrentQuestionTime();
		}

		function handleWindowBlur() {
			commitCurrentQuestionTime();
		}

		function handleWindowFocus() {
			resumeCurrentQuestionTime();
		}

		document.addEventListener('visibilitychange', handleVisibilityChange);
		window.addEventListener('pagehide', handlePageHide);
		window.addEventListener('blur', handleWindowBlur);
		window.addEventListener('focus', handleWindowFocus);

		return () => {
			commitCurrentQuestionTime();
			document.removeEventListener('visibilitychange', handleVisibilityChange);
			window.removeEventListener('pagehide', handlePageHide);
			window.removeEventListener('blur', handleWindowBlur);
			window.removeEventListener('focus', handleWindowFocus);
		};
	}, []);
	const isLowTime = remainingSeconds !== null && remainingSeconds <= 10 * 60;
	const activeHint = activeQuestion ? hintFeedbacks[activeQuestion.question_id] : '';
	const activeReview = activeQuestion ? reviewFeedbacks[activeQuestion.question_id] : '';
	const answeredCount = useMemo(
		() => flatQuestions.filter((question) => hasAnswerValue(answers[question.question_id])).length,
		[answers, flatQuestions],
	);
	const remainingQuestionCount = Math.max(flatQuestions.length - answeredCount, 0);
	const progressPercent = flatQuestions.length > 0 ? Math.round((answeredCount / flatQuestions.length) * 100) : 0;

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
		if (isPracticeMode && checkedResults[questionId]) {
			return;
		}

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
			commitCurrentQuestionTime();
			const studentAnswerRecords = buildStudentAnswerRecords();

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
						question_id: question.question_id,
						question_index: question.question_index,
						type: question.type,
						content: question.content,
						options: question.options,
						statements: question.statements,
						answer: question.answer ?? '',
						student_answer: answers[question.question_id] ?? '',
						has_image: question.has_image,
						image_url: question.image_url,
					})),
				})),
			};

			const result = await submitExam(authToken, {
				student_id: student.id,
				exam_id: exam.exam_id,
				time_taken_seconds: timeTakenSeconds,
				student_ans: studentAnswerRecords,
				full_exam: fullExam,
			});

			cacheExamQuestionTimings(exam.exam_id, getQuestionTimeSecondsMap());
			cacheExamResult(exam.exam_id, result);
			updateStudent({ is_first_login: false });
			router.push(`/exams/${exam.exam_id}/results`);
		} catch (error) {
			setSubmitError(getApiErrorMessage(error, 'Nộp bài thất bại. Vui lòng thử lại sau.'));
			setIsSubmitting(false);
		}
	}, [answers, exam, isSubmitting, router]);

	const handleCheckCurrentQuestion = useCallback(async () => {
		if (!exam || !activeQuestion || checkingQuestionId) {
			return;
		}

		const token = getToken();
		if (!token) {
			router.replace('/login');
			return;
		}

		setCheckError('');
		setCheckingQuestionId(activeQuestion.question_id);
		try {
			const result = await checkPracticeQuestion(token, {
				exam_id: exam.exam_id,
				question_id: activeQuestion.question_id,
				student_answer: answers[activeQuestion.question_id] ?? '',
			});
			setCheckedResults((prev) => ({
				...prev,
				[activeQuestion.question_id]: result,
			}));
		} catch {
			setCheckError('Không thể kiểm tra câu này. Vui lòng thử lại.');
		} finally {
			setCheckingQuestionId(null);
		}
	}, [activeQuestion, answers, checkingQuestionId, exam, router]);

	const handleAskHint = useCallback(async () => {
		if (!activeQuestion || !exam || loadingHintQuestionId || hintFeedbacks[activeQuestion.question_id]) {
			return;
		}

		const token = getToken();
		if (!token) {
			router.replace('/login');
			return;
		}

		setHintError('');
		setLoadingHintQuestionId(activeQuestion.question_id);
		try {
			const data = await askHint(token, {
				exam_id: exam.exam_id,
				question_id: activeQuestion.question_id,
			});
			setHintFeedbacks((prev) => ({
				...prev,
				[activeQuestion.question_id]: data.feedback,
			}));
		} catch (error) {
			setHintError(getApiErrorMessage(error, 'Không thể lấy gợi ý lúc này. Vui lòng thử lại.'));
		} finally {
			setLoadingHintQuestionId(null);
		}
	}, [activeQuestion, exam, hintFeedbacks, loadingHintQuestionId, router]);

	const handleReviewMistake = useCallback(async () => {
		if (!activeQuestion || loadingReviewQuestionId || reviewFeedbacks[activeQuestion.question_id]) {
			return;
		}

		const checkedCurrent = checkedResults[activeQuestion.question_id];
		if (!checkedCurrent) {
			return;
		}

		const token = getToken();
		if (!token) {
			router.replace('/login');
			return;
		}

		setReviewError('');
		setLoadingReviewQuestionId(activeQuestion.question_id);
		try {
			const data = await reviewMistake(token, {
				question_id: activeQuestion.question_id,
				student_ans: checkedCurrent.student_answer,
			});
			setReviewFeedbacks((prev) => ({
				...prev,
				[activeQuestion.question_id]: data.feedback,
			}));
		} catch (error) {
			setReviewError(getApiErrorMessage(error, 'Không thể lấy giải thích lúc này. Vui lòng thử lại.'));
		} finally {
			setLoadingReviewQuestionId(null);
		}
	}, [activeQuestion, checkedResults, loadingReviewQuestionId, reviewFeedbacks, router]);

	function openSubmitConfirm() {
		if (isSubmitting) {
			return;
		}

		setShowSubmitConfirm(true);
	}

	function openExitConfirm() {
		if (isSubmitting) {
			return;
		}

		setShowExitConfirm(true);
	}

	function handleExitExamRoom() {
		setShowExitConfirm(false);
		clearExamRuntimeCache(examId);
		router.push('/documents');
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

	if (loading) {
		return <main className="exam-room">Đang tải đề thi...</main>;
	}

	if (error || !exam || !activeQuestion) {
		return (
			<main className="exam-room">
				<p className="documents-error">{error || 'Không có dữ liệu đề thi.'}</p>
				{isPracticeMode ? (
					<button type="button" className="btn-ghost" onClick={handlePracticeDiscard}>
						Về luyện tập
					</button>
				) : (
					<Link href="/documents" className="btn-ghost">
						Quay lại
					</Link>
				)}
			</main>
		);
	}

	const checkedCurrentQuestion = checkedResults[activeQuestion.question_id];
	const isCurrentQuestionLocked = isPracticeMode && Boolean(checkedCurrentQuestion);

	return (
		<main className="exam-room">
			<header className="exam-header">
				<div className="exam-header-main">
					<p className="documents-kicker">Phòng thi</p>
					<h1 className="documents-title">{exam.subject} - {exam.exam_type}</h1>
					<p className="text-soft">
						{exam.grade ? `Lớp ${exam.grade} | ` : ''}
						{exam.total_questions} câu | {exam.duration_minutes} phút
					</p>
					<div className="exam-progress-strip" aria-label="Tiến độ làm bài">
						<div className="exam-progress-copy">
							<strong>Đã làm {answeredCount}/{flatQuestions.length} câu</strong>
							<span>Còn {remainingQuestionCount} câu • {progressPercent}%</span>
						</div>
						<div className="exam-progress-bar" aria-hidden="true">
							<span style={{ width: `${progressPercent}%` }} />
						</div>
					</div>
				</div>
				{isPracticeMode ? (
					<button type="button" className="btn-ghost" onClick={handlePracticeDiscard}>
						Thoát luyện tập
					</button>
				) : (
					<button type="button" className="btn-danger exam-exit-btn" onClick={openExitConfirm}>
						Thoát phòng thi
					</button>
				)}
			</header>

			<section className="exam-layout">
				<article className="exam-main">
					<div className="exam-question-shell">
						<ExamQuestionHeader
							questionIndex={activeQuestion.index}
							showHintButton={isPracticeMode}
							onAskHint={handleAskHint}
							isHintLoading={loadingHintQuestionId === activeQuestion.question_id}
							hasHint={Boolean(activeHint)}
							showReviewButton={isPracticeMode && Boolean(checkedCurrentQuestion)}
							onReviewMistake={handleReviewMistake}
							isReviewLoading={loadingReviewQuestionId === activeQuestion.question_id}
							hasReview={Boolean(activeReview)}
						/>

						<div className="exam-question-content"><MathText text={activeQuestion.question.content} /></div>

						<QuestionFeedbackPanels
							hintError={hintError}
							hintFeedback={activeHint}
							reviewError={reviewError}
							reviewFeedback={activeReview}
						/>

						{activeQuestion.question.has_image && activeQuestion.question.image_url ? (
							<div className="exam-image-wrap">
								<img src={activeQuestion.question.image_url} alt={`Câu ${activeQuestion.index}`} className="exam-image" />
							</div>
						) : null}

						<EditableAnswerPanel
							question={activeQuestion}
							answer={answers[activeQuestion.question_id] ?? ''}
							onChange={(value) => setAnswer(activeQuestion.question_id, value)}
							disabled={isCurrentQuestionLocked}
						/>

						{isPracticeMode && checkedCurrentQuestion ? (
							<div className={`exam-result-short ${checkedCurrentQuestion.is_correct ? 'is-correct' : 'is-wrong'}`}>
								<p>
									<strong>Kết quả:</strong> {checkedCurrentQuestion.is_correct ? 'Đúng' : 'Sai'}
								</p>
								<p>
									<strong>Đáp án đúng:</strong> {checkedCurrentQuestion.correct_answer || 'Chưa có'}
								</p>
							</div>
						) : null}
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
							const answered = Boolean(answers[item.question_id]);
							const checkedResult = checkedResults[item.question_id];
							const stateClass = checkedResult
								? (checkedResult.is_correct ? 'is-correct' : 'is-wrong')
								: answered
									? 'is-answered'
									: 'is-unanswered';

							return (
								<button
									key={item.question_id}
									type="button"
									className={`exam-index-btn ${stateClass} ${active ? 'is-active' : ''}`}
									onClick={() => setActiveQuestionIndex(idx)}
								>
									{item.index}
								</button>
							);
						})}
					</div>

					<div className="exam-submit-wrap">
						{isPracticeMode ? (
							<>
								<button
									type="button"
									className="exam-submit-btn"
									onClick={handleCheckCurrentQuestion}
									disabled={checkingQuestionId === activeQuestion.question_id || isCurrentQuestionLocked || isCompletingPractice}
								>
									{checkingQuestionId === activeQuestion.question_id ? (
										<>
											<span className="exam-submit-spinner" aria-hidden="true" />
											Đang check...
										</>
									) : isCurrentQuestionLocked ? (
										'Đã check câu này'
									) : (
										'Check câu này'
									)}
								</button>
								<button
									type="button"
									className="exam-submit-btn"
									onClick={handlePracticeComplete}
									disabled={isCompletingPractice}
								>
									{isCompletingPractice ? (
										<>
											<span className="exam-submit-spinner" aria-hidden="true" />
											Đang hoàn tất...
										</>
									) : (
										'Xong'
									)}
								</button>
								<button
									type="button"
									className="btn-danger exam-submit-side-btn"
									onClick={handlePracticeDiscard}
									disabled={isCompletingPractice}
								>
									Thoát không lưu
								</button>
								{checkError ? <p className="documents-error exam-submit-error">{checkError}</p> : null}
								{practiceCompleteError ? <p className="documents-error exam-submit-error">{practiceCompleteError}</p> : null}
							</>
						) : (
							<>
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
							</>
						)}
					</div>
				</aside>
			</section>

			{!isPracticeMode && showSubmitConfirm ? (
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

			{!isPracticeMode && showExitConfirm ? (
				<div className="exam-submit-confirm-overlay" role="dialog" aria-modal="true" aria-labelledby="exit-confirm-title">
					<div className="exam-submit-confirm-card exam-exit-confirm-card">
						<p className="exam-exit-confirm-kicker">Cảnh báo</p>
						<h3 id="exit-confirm-title">Thoát phòng thi?</h3>
						<p>
							Nếu thoát phòng thi lúc này, bài làm hiện tại sẽ không được lưu lại.
						</p>
						<div className="exam-submit-confirm-actions">
							<button
								type="button"
								className="btn-ghost"
								onClick={() => setShowExitConfirm(false)}
								disabled={isSubmitting}
							>
								Ở lại làm bài
							</button>
							<button
								type="button"
								className="btn-danger"
								onClick={handleExitExamRoom}
								disabled={isSubmitting}
							>
								Thoát và bỏ bài làm
							</button>
						</div>
					</div>
				</div>
			) : null}
		</main>
	);
}
