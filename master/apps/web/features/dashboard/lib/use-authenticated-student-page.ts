'use client';

import { getCurrentStudent } from '@/shared/api/client';
import { getApiErrorMessage, isInvalidSessionError } from '@/shared/api/error-message';
import { clearAuth, getToken, saveStudent } from '@/shared/auth/storage';
import { Student } from '@/shared/models/student';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

type UseAuthenticatedStudentPageResult = {
	student: Student | null;
	loading: boolean;
	error: string;
	logout: () => void;
};

export function useAuthenticatedStudentPage(fallbackError: string): UseAuthenticatedStudentPageResult {
	const router = useRouter();
	const [student, setStudent] = useState<Student | null>(null);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState('');

	useEffect(() => {
		const token = getToken();
		if (!token) {
			router.replace('/login');
			return;
		}
		const authToken = token;

		let cancelled = false;

		async function loadStudent() {
			setLoading(true);
			setError('');

			try {
				const currentStudent = await getCurrentStudent(authToken);
				if (cancelled) {
					return;
				}

				setStudent(currentStudent);
				saveStudent(currentStudent);
			} catch (requestError: unknown) {
				if (isInvalidSessionError(requestError)) {
					clearAuth();
					router.replace('/login');
					return;
				}

				if (!cancelled) {
					setError(getApiErrorMessage(requestError, fallbackError));
				}
			} finally {
				if (!cancelled) {
					setLoading(false);
				}
			}
		}

		void loadStudent();

		return () => {
			cancelled = true;
		};
	}, [fallbackError, router]);

	function logout() {
		clearAuth();
		router.replace('/login');
	}

	return {
		student,
		loading,
		error,
		logout,
	};
}
