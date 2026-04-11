import { ExamDetail } from '../types';

const baseExam: ExamDetail = {
	exam_id: 'doc-001',
	source_type: 'documents_library',
	subject: 'Toán Học',
	exam_type: 'THPTQG_2025',
	total_questions: 6,
	duration_minutes: 1,
	sections: [
		{
			type: 'multiple_choice',
			section_name: 'Phan I: Trắc nghiệm khách quan 4 lựa chọn',
			questions: [
				{
					id: 'q1',
					question_index: 1,
					type: 'multiple_choice',
					content: 'Tim nguyên hàm của f(x) = $2x + 1$ trên $\\mathbb{R}$.',
					options: ['A. $x^2 + x + C$', 'B. $x^2 + C$', 'C. $2x^2 + x + C$', 'D. $x + C$'],
					correct_answer: 'A',
					has_image: false,
					topic_tags: ['math.12.integrals'],
				},
				{
					id: 'q2',
					question_index: 2,
					type: 'multiple_choice',
					content: 'Đạo hàm của hàm số y = $x^3$ là?',
					options: ['A. $x^2$', 'B. $3x^2$', 'C. $3x$', 'D. $x^3$'],
					correct_answer: 'B',
					has_image: false,
					topic_tags: ['math.12.derivatives'],
				},
			],
		},
		{
			type: 'true_false',
			section_name: 'Phan II: Đúng sai',
			questions: [
				{
					id: 'q3',
					question_index: 3,
					type: 'true_false',
					content: 'Cho hàm số y = f(x) có đồ thị như hình vẽ...',
					statements: [
						'a) Hàm số đồng biến trên khoảng $(0;2)$',
						'b) Giá trị cực trị tại x = 1',
						'c) Đồ thị cắt trục hoành tại 3 điểm',
						"d) $y'$ = 0 có nghiệm kép",
					],
					correct_answer: 'T,F,T,F',
					has_image: true,
					image_url: 'https://img.dolenglish.vn/rs:auto:::0/w:820/q:90/format:webp/aHR0cHM6Ly9tZWRpYS5kb2xlbmdsaXNoLnZuL1BVQkxJQy9GUk9NX1VSTC8xNUgxR25rS2J1dVdLcmJ4VGhMU0w3bVlXRGJDdFBMcU1fMjAyNi0wMi0wNDE3MzExNS5wbmc=',
					topic_tags: ['math.12.functions'],
				},
				{
					id: 'q4',
					question_index: 4,
					type: 'true_false',
					content: 'Cho cấp số cộng $(u_n) với u_1 = 2, d = 3$.',
					statements: [
						'a) $u_2 = 5$',
						'b) $u_5 = 14$',
						'c) Tổng 5 số hạng đầu là 40',
						'd) $u_n = 2 + 3n$',
					],
					correct_answer: 'T,T,T,F',
					has_image: false,
					topic_tags: ['math.11.sequence'],
				},
			],
		},
		{
			type: 'short_answer',
			section_name: 'Phan III: Trả lời ngắn',
			questions: [
				{
					id: 'q5',
					question_index: 5,
					type: 'short_answer',
					content: 'Bán kính mặt cầu nội tiếp hình lập phương cạnh a = 4 là bao nhiêu?',
					has_image: false,
					correct_answer: '2',
					topic_tags: ['math.12.geometry'],
				},
				{
					id: 'q6',
					question_index: 6,
					type: 'short_answer',
					content: 'Tính giá trị biểu thức: 2 + 3 x 4.',
					has_image: false,
					correct_answer: '14',
					topic_tags: ['math.10.arithmetic'],
				},
			],
		},
	],
};

export const MOCK_EXAMS_BY_DOCUMENT_ID: Record<string, ExamDetail> = {
	'doc-001': baseExam,
	'doc-002': { ...baseExam, exam_id: 'doc-002' },
	'doc-003': { ...baseExam, exam_id: 'doc-003', subject: 'Toán Học' },
	'doc-004': { ...baseExam, exam_id: 'doc-004', subject: 'Toán Học' },
	'doc-005': { ...baseExam, exam_id: 'doc-005', subject: 'Toán Học' },
};
