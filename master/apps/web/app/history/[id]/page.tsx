'use client';

import { QuestionFeedbackPanels } from '@/features/exams/components/feedback-panels';
import { formatDateTime, formatScore } from '@/features/exams/lib/helpers';
import { MathText } from '@/features/exams/components/math-text';
import { ExamQuestionHeader } from '@/features/exams/components/question-header';
import { ResultAnswerPanel } from '@/features/exams/components/result-answer-panel';
import { FlatQuestion, flattenExamSections } from '@/features/exams/lib/types';
import {
	AskHintResponse,
	ExamEvaluationItem,
	HistoryDetailResponse,
	askHint,
	getHistoryDetail,
	reviewMistake,
} from '@/shared/api/client';
import { getApiErrorMessage } from '@/shared/api/error-message';
import { getToken } from '@/shared/auth/storage';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useCallback, useEffect, useMemo, useState } from 'react';

function intentToLabel(intent: HistoryDetailResponse['intent']) {
	return intent === 'EXAM_PRACTICE' ? 'Luyện tập' : 'Đề thi';
}

export default function HistoryDetailPage() {
	const router = useRouter();
	const params = useParams<{ id: string }>();
	const historyId = typeof params?.id === 'string' ? params.id : '';

	const [history, setHistory] = useState<HistoryDetailResponse | null>(null);
	const [error, setError] = useState('');
	const [loading, setLoading] = useState(true);
	const [activeQuestionIndex, setActiveQuestionIndex] = useState(0);
	const [hintFeedbacks, setHintFeedbacks] = useState<Record<string, AskHintResponse>>({});
	const [loadingHintQuestionId, setLoadingHintQuestionId] = useState<string | null>(null);
	const [hintError, setHintError] = useState('');
	const [reviewFeedbacks, setReviewFeedbacks] = useState<Record<string, string>>({});
	const [loadingReviewQuestionId, setLoadingReviewQuestionId] = useState<string | null>(null);
	const [reviewError, setReviewError] = useState('');

	useEffect(() => {
		if (!historyId) {
			setError('Không tìm thấy lịch sử bài làm.');
			setLoading(false);
			return;
		}

		const token = getToken();
		if (!token) {
			router.replace('/login');
			return;
		}
		const authToken = token;

		async function loadHistoryDetail() {
			setLoading(true);
			setError('');

			try {
				const data = await getHistoryDetail(historyId, authToken);
				setHistory(data);
			} catch {
				setError('Không tải được chi tiết bài làm.');
			} finally {
				setLoading(false);
			}
		}

		loadHistoryDetail();
	}, [historyId, router]);

	const flatQuestions = useMemo<FlatQuestion[]>(() => {
		if (!history) {
			return [];
		}

		return flattenExamSections(history.sections);
	}, [history]);

	const evaluationMap = useMemo(() => {
		if (!history) {
			return new Map<string, ExamEvaluationItem>();
		}

		return new Map(history.evaluation.per_question.map((item) => [item.question_id, item]));
	}, [history]);

	const activeQuestion = flatQuestions[activeQuestionIndex];
	const activeEvaluation = activeQuestion ? evaluationMap.get(activeQuestion.question_id) : null;
	const activeHint = activeQuestion ? hintFeedbacks[activeQuestion.question_id]?.feedback ?? '' : '';
	const activeHintLevels = activeQuestion ? hintFeedbacks[activeQuestion.question_id]?.hints : undefined;
	const activeReview = activeQuestion ? reviewFeedbacks[activeQuestion.question_id] : '';
	const scoreSummaryValue = history?.score !== null && history?.score !== undefined
		? formatScore(history.score)
		: `${history?.correct_count ?? 0}/${history?.evaluation.total_questions ?? 0}`;
	const scoreSummaryLabel = history?.score !== null && history?.score !== undefined
		? 'Điểm tổng'
		: 'Số câu đúng';
	const scoreSummaryMeta = history?.score !== null && history?.score !== undefined
		? ''
		: 'Câu đúng trên tổng số câu';

	const handleAskHint = useCallback(async () => {
		if (!activeQuestion || !history || loadingHintQuestionId || hintFeedbacks[activeQuestion.question_id]) {
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
				exam_id: history.exam_id,
				question_id: activeQuestion.question_id,
			});
			setHintFeedbacks((prev) => ({
				...prev,
				[activeQuestion.question_id]: data,
			}));
		} catch (error) {
			setHintError(getApiErrorMessage(error, 'Không thể lấy gợi ý lúc này. Vui lòng thử lại.'));
		} finally {
			setLoadingHintQuestionId(null);
		}
	}, [activeQuestion, hintFeedbacks, history, loadingHintQuestionId, router]);

	const handleReviewMistake = useCallback(async () => {
		if (!activeQuestion || !activeEvaluation || loadingReviewQuestionId || reviewFeedbacks[activeQuestion.question_id]) {
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
				student_ans: activeEvaluation.student_answer,
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
	}, [activeEvaluation, activeQuestion, loadingReviewQuestionId, reviewFeedbacks, router]);

	if (loading) {
		return <main className="exam-room">Đang tải bài làm...</main>;
	}

	if (error || !history || !activeQuestion || !activeEvaluation) {
		return (
			<main className="exam-room">
				<p className="documents-error">{error || 'Không có dữ liệu bài làm.'}</p>
				<Link href="/dashboard" className="btn-primary">
					Quay lại tổng quan
				</Link>
			</main>
		);
	}

	return (
		<main className="exam-room exam-result-room">
			<header className="exam-header exam-result-header">
				<div className="exam-header-main">
					<p className="documents-kicker">Xem lại bài làm</p>
					<h1 className="documents-title">{history.subject} - {history.exam_type}</h1>
					<p className="text-soft">
						{history.grade ? `Lớp ${history.grade} | ` : ''}
						{intentToLabel(history.intent)} | {formatDateTime(history.created_at)}
					</p>
				</div>
				<div className="exam-header-side">
					<Link href="/dashboard" className="btn-ghost">Về tổng quan</Link>
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
							isHintLoading={loadingHintQuestionId === activeQuestion.question_id}
							hasHint={Boolean(activeHint)}
							showReviewButton
							onReviewMistake={handleReviewMistake}
							isReviewLoading={loadingReviewQuestionId === activeQuestion.question_id}
							hasReview={Boolean(activeReview)}
							statusText={activeEvaluation.is_correct ? 'Trả lời đúng' : 'Trả lời sai'}
							statusTone={activeEvaluation.is_correct ? 'is-correct' : 'is-wrong'}
						/>

						<div className="exam-question-content"><MathText text={activeQuestion.question.content} /></div>

						<QuestionFeedbackPanels
							hintError={hintError}
							hintFeedback={activeHint}
							hintLevels={activeHintLevels}
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
							const evaluation = evaluationMap.get(item.question_id);
							const stateClass = !evaluation?.student_answer
								? 'is-unanswered'
								: evaluation.is_correct
									? 'is-correct'
									: 'is-wrong';

							return (
								<button
									key={item.question_id}
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
