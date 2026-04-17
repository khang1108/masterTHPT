'use client';

import { QuestionFeedbackPanels } from '@/features/exams/components/feedback-panels';
import { formatScore } from '@/features/exams/lib/helpers';
import { MathText } from '@/features/exams/components/math-text';
import { ExamQuestionHeader } from '@/features/exams/components/question-header';
import { ResultAnswerPanel } from '@/features/exams/components/result-answer-panel';
import { FlatQuestion, flattenExamSections } from '@/features/exams/lib/types';
import { DocumentDetailResponse, ExamEvaluationItem, askHint, createHistory, getDocumentDetail, reviewMistake } from '@/shared/api/client';
import { getApiErrorMessage } from '@/shared/api/error-message';
import { getToken } from '@/shared/auth/storage';
import {
	clearExamRuntimeCache,
	getCachedExamDetail,
	getCachedExamQuestionTimings,
	getCachedExamResult,
} from '@/features/exams/lib/exam-runtime-store';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useCallback, useEffect, useMemo, useState } from 'react';

export default function ExamResultPage() {
	const router = useRouter();
	const params = useParams<{ id: string }>();
	const examId = typeof params?.id === 'string' ? params.id : '';

	const [exam, setExam] = useState<DocumentDetailResponse | null>(null);
	const [error, setError] = useState('');
	const [loading, setLoading] = useState(true);
	const [activeQuestionIndex, setActiveQuestionIndex] = useState(0);
	const [hintFeedbacks, setHintFeedbacks] = useState<Record<string, string>>({});
	const [loadingHintQuestionId, setLoadingHintQuestionId] = useState<string | null>(null);
	const [hintError, setHintError] = useState('');
	const [reviewFeedbacks, setReviewFeedbacks] = useState<Record<string, string>>({});
	const [loadingReviewQuestionId, setLoadingReviewQuestionId] = useState<string | null>(null);
	const [reviewError, setReviewError] = useState('');

	const result = useMemo(() => {
		if (!examId) {
			return null;
		}

		return getCachedExamResult(examId);
	}, [examId]);

	useEffect(() => {
		if (!examId) {
			setError('Không tìm thấy mã đề thi.');
			setLoading(false);
			return;
		}

		if (!result) {
			setError('Không tìm thấy kết quả. Vui lòng nộp bài từ phòng thi trước.');
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

			try {
				const cachedExam = getCachedExamDetail(examId);
				if (cachedExam) {
					setExam(cachedExam);
					return;
				}

				const data = await getDocumentDetail(examId, authToken);
				setExam(data);
			} catch {
				setError('Không tải được dữ liệu đề thi.');
			} finally {
				setLoading(false);
			}
		}

		loadExam();
	}, [examId, result, router]);

	const flatQuestions = useMemo<FlatQuestion[]>(() => {
		if (!exam) {
			return [];
		}

		return flattenExamSections(exam.sections);
	}, [exam]);

	const evaluationMap = useMemo(() => {
		if (!result) {
			return new Map<string, ExamEvaluationItem>();
		}

		return new Map(result.per_question.map((item) => [item.question_id, item]));
	}, [result]);

	const activeQuestion = flatQuestions[activeQuestionIndex];
	const activeEvaluation = activeQuestion ? evaluationMap.get(activeQuestion.id) : null;
	const activeHint = activeQuestion ? hintFeedbacks[activeQuestion.id] : '';
	const activeReview = activeQuestion ? reviewFeedbacks[activeQuestion.id] : '';
	const scoreSummaryValue = result?.score !== null && result?.score !== undefined
		? formatScore(result.score)
		: `${result?.correct_count ?? 0}/${result?.total_questions ?? 0}`;
	const scoreSummaryLabel = result?.score !== null && result?.score !== undefined
		? 'Điểm tổng'
		: 'Số câu đúng';
	const scoreSummaryMeta = result?.score !== null && result?.score !== undefined
		? ''
		: 'Câu đúng trên tổng số câu';

	const handleExitResults = useCallback(async () => {
		const token = getToken();
		if (!token || !examId) {
			if (examId) {
				clearExamRuntimeCache(examId);
			}

			router.push('/documents');
			return;
		}

		const questionTimings = getCachedExamQuestionTimings(examId);
		const studentAnswers = result?.per_question.map((item) => ({
			question_id: item.question_id,
			student_answer: item.student_answer,
			time_spent_seconds: questionTimings[item.question_id] ?? 0,
		})) ?? [];

		try {
			await createHistory(token, {
				intent: 'VIEW_ANALYSIS',
				exam_id: examId,
				student_ans: studentAnswers,
				correct_count: result?.correct_count ?? 0,
				score: result?.score ?? undefined,
			});
		} catch {
			// Keep exit smooth even if history write fails.
		} finally {
			clearExamRuntimeCache(examId);
			router.push('/documents');
		}
	}, [examId, result, router]);

	const handleAskHint = useCallback(async () => {
		if (!activeQuestion || !examId || loadingHintQuestionId || hintFeedbacks[activeQuestion.id]) {
			return;
		}

		const token = getToken();
		if (!token) {
			router.replace('/login');
			return;
		}

		setHintError('');
		setLoadingHintQuestionId(activeQuestion.id);
		try {
			const data = await askHint(token, {
				exam_id: examId,
				question_id: activeQuestion.id,
			});
			setHintFeedbacks((prev) => ({
				...prev,
				[activeQuestion.id]: data.feedback,
			}));
		} catch (error) {
			setHintError(getApiErrorMessage(error, 'Không thể lấy gợi ý lúc này. Vui lòng thử lại.'));
		} finally {
			setLoadingHintQuestionId(null);
		}
	}, [activeQuestion, examId, hintFeedbacks, loadingHintQuestionId, router]);

	const handleReviewMistake = useCallback(async () => {
		if (!activeQuestion || !activeEvaluation || loadingReviewQuestionId || reviewFeedbacks[activeQuestion.id]) {
			return;
		}

		const token = getToken();
		if (!token) {
			router.replace('/login');
			return;
		}

		setReviewError('');
		setLoadingReviewQuestionId(activeQuestion.id);
		try {
			const data = await reviewMistake(token, {
				question_id: activeQuestion.id,
				student_ans: activeEvaluation.student_answer,
			});
			setReviewFeedbacks((prev) => ({
				...prev,
				[activeQuestion.id]: data.feedback,
			}));
		} catch (error) {
			setReviewError(getApiErrorMessage(error, 'Không thể lấy giải thích lúc này. Vui lòng thử lại.'));
		} finally {
			setLoadingReviewQuestionId(null);
		}
	}, [activeEvaluation, activeQuestion, loadingReviewQuestionId, reviewFeedbacks, router]);

	if (loading) {
		return <main className="exam-room">Đang tải kết quả...</main>;
	}

	if (error || !exam || !result || !activeQuestion || !activeEvaluation) {
		return (
			<main className="exam-room">
				<p className="documents-error">{error || 'Không có dữ liệu kết quả.'}</p>
				<Link href={`/exams/${examId}`} className="btn-primary">
					Quay lại phòng thi
				</Link>
			</main>
		);
	}

	return (
		<main className="exam-room exam-result-room">
			<header className="exam-header exam-result-header">
				<div className="exam-header-main">
					<p className="documents-kicker">Kết quả bài thi</p>
					<h1 className="documents-title">{exam.subject} - {exam.exam_type}</h1>
					<p className="text-soft">
						{exam.grade ? `Lớp ${exam.grade} | ` : ''}
						{exam.total_questions} câu | {exam.duration_minutes} phút
					</p>
				</div>
				<div className="exam-header-side">
					<button type="button" className="btn-ghost" onClick={handleExitResults}>
						Về Kho đề
					</button>
					<div className="exam-result-hero">
						<p className="exam-result-hero-label">{scoreSummaryLabel}</p>
						<p className="exam-result-hero-value">{scoreSummaryValue}</p>
						{scoreSummaryMeta ? (
							<p className="exam-result-hero-meta">{scoreSummaryMeta}</p>
						) : null}
					</div>
				</div>
			</header>

			<section className="exam-layout">
				<article className="exam-main">
					<div className="exam-question-shell">
						<ExamQuestionHeader
							questionIndex={activeQuestion.index}
							showHintButton
							onAskHint={handleAskHint}
							isHintLoading={loadingHintQuestionId === activeQuestion.id}
							hasHint={Boolean(activeHint)}
							showReviewButton
							onReviewMistake={handleReviewMistake}
							isReviewLoading={loadingReviewQuestionId === activeQuestion.id}
							hasReview={Boolean(activeReview)}
							statusText={activeEvaluation.is_correct ? 'Trả lời đúng' : 'Trả lời sai'}
							statusTone={activeEvaluation.is_correct ? 'is-correct' : 'is-wrong'}
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

						<ResultAnswerPanel question={activeQuestion} evaluation={activeEvaluation} />
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
					<h3>Kết quả từng câu</h3>
					<div className="exam-index-grid">
						{flatQuestions.map((item, idx) => {
							const isActive = idx === activeQuestionIndex;
							const evaluation = evaluationMap.get(item.id);
							const stateClass = !evaluation?.student_answer
								? 'is-unanswered'
								: evaluation.is_correct
									? 'is-correct'
									: 'is-wrong';

							return (
								<button
									key={item.id}
									type="button"
									className={`exam-index-btn ${stateClass} ${isActive ? 'is-active' : ''}`}
									onClick={() => setActiveQuestionIndex(idx)}
								>
									{item.index}
								</button>
							);
						})}
					</div>
				</aside>
			</section>
		</main>
	);
}
