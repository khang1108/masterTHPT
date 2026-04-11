export type DocumentItem = {
	id: string;
	title: string;
	subject: string;
	year: number;
	exam_type: string;
	type: string;
};

export type ExamQuestion = {
	id: string;
	question_index: number;
	type: 'multiple_choice' | 'true_false' | 'short_answer';
	content: string;
	options?: string[];
	statements?: string[];
	correct_answer: string;
	has_image: boolean;
	image_url?: string;
	topic_tags?: string[];
};

export type ExamSection = {
	type: 'multiple_choice' | 'true_false' | 'short_answer';
	section_name: string;
	questions: ExamQuestion[];
};

export type ExamDetail = {
	exam_id: string;
	source_type: string;
	subject: string;
	exam_type: string;
	total_questions: number;
	duration_minutes: number;
	sections: ExamSection[];
};
