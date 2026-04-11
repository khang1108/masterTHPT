'use client';

import { DocumentDetailResponse, ExamEvaluationItem, ExamQuestion, getDocumentDetail } from '@/lib/api';
import { getToken } from '@/lib/auth';
import { getCachedExamDetail, getCachedExamResult } from '@/lib/exam-session';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';
import Latex from 'react-latex-next';

type FlatQuestion = {
	id: string;
	index: number;
	sectionType: 'multiple_choice' | 'true_false' | 'short_answer';
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

function tokenToLabel(value: string) {
	return value === 'T' ? 'Đúng' : 'Sai';
}

export default function ExamResultPage() {
	const router = useRouter();
	const params = useParams<{ id: string }>();
	const examId = typeof params?.id === 'string' ? params.id : '';

	const [exam, setExam] = useState<DocumentDetailResponse | null>(null);
	const [error, setError] = useState('');
	const [loading, setLoading] = useState(true);
	const [activeQuestionIndex, setActiveQuestionIndex] = useState(0);

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

		return exam.sections.flatMap((section) =>
			section.questions.map((question) => ({
				id: question.id,
				index: question.question_index,
				sectionType: section.type,
				question,
			})),
		);
	}, [exam]);

	const evaluationMap = useMemo(() => {
		if (!result) {
			return new Map<string, ExamEvaluationItem>();
		}

		return new Map(result.per_question.map((item) => [item.question_id, item]));
	}, [result]);

	const activeQuestion = flatQuestions[activeQuestionIndex];
	const activeEvaluation = activeQuestion ? evaluationMap.get(activeQuestion.id) : null;

	function renderResultPanel(question: FlatQuestion, evaluation: ExamEvaluationItem) {
		if (question.sectionType === 'multiple_choice') {
			const selected = evaluation.student_answer.trim();
			const correctLabel = parseOption(evaluation.correct_answer).label;

			return (
				<div className="exam-mc-grid exam-result-panel">
					{question.question.options?.map((option) => {
						const parsed = parseOption(option);
						const isCorrectOption = parsed.label === correctLabel;
						const isStudentSelected = selected === parsed.label;
						const isWrongSelected = isStudentSelected && !isCorrectOption;

						return (
							<div
								key={`${question.id}-${parsed.label}`}
								className={`exam-mc-option exam-result-option ${isCorrectOption ? 'is-correct' : ''} ${isWrongSelected ? 'is-wrong' : ''}`}
							>
								<div className="exam-mc-option-main">
									<span className="exam-mc-badge">{parsed.label}</span>
									<MathText text={parsed.text} />
								</div>
								<span className="exam-result-tag">{isCorrectOption ? 'Đúng' : isStudentSelected ? 'Bạn chọn' : ''}</span>
							</div>
						);
					})}
				</div>
			);
		}

		if (question.sectionType === 'true_false') {
			const statements = question.question.statements ?? [];
			const studentTokens = evaluation.student_answer.split(',').map((item) => item.trim());
			const correctTokens = evaluation.correct_answer.split(',').map((item) => item.trim());

			return (
				<div className="exam-tf-table exam-result-panel">
					<div className="exam-tf-head exam-tf-result-head">
						<p>PHÁT BIỂU</p>
						<p>BẠN CHỌN</p>
						<p>ĐÁP ÁN</p>
					</div>

					{statements.map((statement, idx) => {
						const studentToken = studentTokens[idx] ?? '';
						const correctToken = correctTokens[idx] ?? '';
						const isCorrect = studentToken === correctToken;

						return (
							<div key={`${question.id}-${idx}`} className={`exam-tf-item exam-tf-result-item ${isCorrect ? 'is-correct' : 'is-wrong'}`}>
								<div className="exam-tf-statement">
									<span className="exam-tf-label">{getAlphabetLabel(idx)}</span>
									<p><MathText text={statement} /></p>
								</div>
								<p className="exam-tf-answer-chip">{studentToken ? tokenToLabel(studentToken) : 'Bỏ trống'}</p>
								<p className="exam-tf-answer-chip is-correct">{correctToken ? tokenToLabel(correctToken) : '-'}</p>
							</div>
						);
					})}
				</div>
			);
		}

		return (
			<div className="exam-short-wrap exam-result-panel">
				<div className={`exam-result-short ${evaluation.is_correct ? 'is-correct' : 'is-wrong'}`}>
					<p><strong>Bạn trả lời:</strong> {evaluation.student_answer || 'Bỏ trống'}</p>
					<p><strong>Đáp án đúng:</strong> {evaluation.correct_answer}</p>
				</div>
			</div>
		);
	}

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

	const scorePercent = Math.round((result.total_score / Math.max(result.max_score, 1)) * 100);

	return (
		<main className="exam-room exam-result-room">
			<header className="exam-header exam-result-header">
				<div>
					<p className="documents-kicker">Kết quả bài thi</p>
					<h1 className="documents-title">{exam.subject} - {exam.exam_type}</h1>
					<p className="text-soft">Tổng điểm: {result.total_score.toFixed(2)} / {result.max_score.toFixed(2)} ({scorePercent}%)</p>
				</div>
				<Link href="/documents" className="btn-ghost">Về Kho đề</Link>
			</header>

			<section className="exam-result-overview">
				<p><strong>Điểm mạnh:</strong> {result.overall_analysis.strengths.join(' | ') || 'Đang cập nhật'}</p>
				<p><strong>Điểm yếu:</strong> {result.overall_analysis.weaknesses.join(' | ') || 'Đang cập nhật'}</p>
				<p><strong>Gợi ý AI:</strong> {result.overall_analysis.general_advice}</p>
			</section>

			<section className="exam-layout">
				<article className="exam-main">
					<div className="exam-question-shell">
						<div className="exam-question-top">
							<div className="exam-question-chip">
								<span>{activeQuestion.index}</span>
								<strong>CÂU {activeQuestion.index}</strong>
							</div>
							<p className={`exam-result-status ${activeEvaluation.is_correct ? 'is-correct' : 'is-wrong'}`}>
								{activeEvaluation.is_correct ? 'Trả lời đúng' : 'Trả lời sai'}
							</p>
						</div>

						<div className="exam-question-content"><MathText text={activeQuestion.question.content} /></div>

						{activeQuestion.question.has_image && activeQuestion.question.image_url ? (
							<div className="exam-image-wrap">
								<img src={activeQuestion.question.image_url} alt={`Câu ${activeQuestion.index}`} className="exam-image" />
							</div>
						) : null}

						{renderResultPanel(activeQuestion, activeEvaluation)}

						<div className="exam-result-explain">
							<p className="exam-result-explain-title">Giải thích AI</p>
							<p>{activeEvaluation.reasoning}</p>
							{activeEvaluation.error_analysis?.remedial ? (
								<p><strong>Khuyến nghị:</strong> {activeEvaluation.error_analysis.remedial}</p>
							) : null}
						</div>
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
							const isCorrect = evaluation?.is_correct ?? false;

							return (
								<button
									key={item.id}
									type="button"
									className={`exam-index-btn ${isActive ? 'is-active' : ''} ${isCorrect ? 'is-correct' : 'is-wrong'}`}
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
