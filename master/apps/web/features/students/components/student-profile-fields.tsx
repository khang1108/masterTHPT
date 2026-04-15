'use client';

import { GRADE_OPTIONS, StudentProfileFormValue } from '@/features/students/lib/student-profile';

type StudentProfileFieldsProps = {
	idPrefix: string;
	value: StudentProfileFormValue;
	disabled?: boolean;
	onChange: (value: StudentProfileFormValue) => void;
};

export function StudentProfileFields({
	idPrefix,
	value,
	disabled = false,
	onChange,
}: StudentProfileFieldsProps) {
	function updateField<Key extends keyof StudentProfileFormValue>(
		key: Key,
		nextValue: StudentProfileFormValue[Key],
	) {
		onChange({
			...value,
			[key]: nextValue,
		});
	}

	return (
		<div className="onboarding-form-grid">
			<div>
				<label className="input-label" htmlFor={`${idPrefix}-name`}>
					Họ và tên
				</label>
				<input
					id={`${idPrefix}-name`}
					type="text"
					className="input-field"
					value={value.name}
					onChange={(event) => updateField('name', event.target.value)}
					disabled={disabled}
					required
				/>
			</div>

			<div>
				<label className="input-label" htmlFor={`${idPrefix}-grade`}>
					Lớp
				</label>
				<select
					id={`${idPrefix}-grade`}
					className="input-field"
					value={value.grade}
					onChange={(event) => updateField('grade', Number(event.target.value) as StudentProfileFormValue['grade'])}
					disabled={disabled}
				>
					{GRADE_OPTIONS.map((option) => (
						<option key={option} value={option}>
							Lớp {option}
						</option>
					))}
				</select>
			</div>

			<div>
				<label className="input-label" htmlFor={`${idPrefix}-school`}>
					Trường
				</label>
				<input
					id={`${idPrefix}-school`}
					type="text"
					className="input-field"
					value={value.school}
					onChange={(event) => updateField('school', event.target.value)}
					disabled={disabled}
					required
				/>
			</div>

			<div className="onboarding-form-full">
				<label className="input-label" htmlFor={`${idPrefix}-goal`}>
					Mục tiêu học tập
				</label>
				<textarea
					id={`${idPrefix}-goal`}
					className="input-field input-textarea"
					value={value.learning_goal}
					onChange={(event) => updateField('learning_goal', event.target.value)}
					disabled={disabled}
					rows={4}
					required
				/>
			</div>
		</div>
	);
}
