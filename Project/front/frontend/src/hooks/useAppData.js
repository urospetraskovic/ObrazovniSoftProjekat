import { useCallback, useEffect, useState } from 'react';

import { courseApi, lessonApi, questionApi, healthApi } from '../api';

const API_STATUS_INTERVAL_MS = 30_000;

export default function useAppData() {
  const [courses, setCourses] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [selectedLesson, setSelectedLesson] = useState(null);
  const [questions, setQuestions] = useState([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [apiStatus, setApiStatus] = useState(null);

  const checkApiStatus = useCallback(async () => {
    try {
      const response = await healthApi.check();
      setApiStatus(response.data);
    } catch (err) {
      // Silent failure for API status check
    }
  }, []);

  const fetchCourses = useCallback(async () => {
    try {
      setLoading(true);
      const response = await courseApi.getAll();
      setCourses(response.data.courses || []);
    } catch (err) {
      setError('Failed to fetch courses');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchQuestions = useCallback(async (courseId = null) => {
    try {
      setLoading(true);
      const response = await questionApi.getAll(courseId);
      setQuestions(response.data.questions || []);
    } catch (err) {
      // Silent failure for questions fetch
    } finally {
      setLoading(false);
    }
  }, []);

  const handleSelectCourse = useCallback(async (course, onSuccess) => {
    try {
      setLoading(true);
      const response = await courseApi.getById(course.id);
      setSelectedCourse(response.data.course);
      setSelectedLesson(null);
      await fetchQuestions(course.id);
      if (onSuccess) onSuccess();
    } catch (err) {
      setError('Failed to fetch course details');
    } finally {
      setLoading(false);
    }
  }, [fetchQuestions]);

  const handleSelectLesson = useCallback(async (lesson, onSuccess) => {
    try {
      setLoading(true);
      const response = await lessonApi.getById(lesson.id);
      setSelectedLesson(response.data.lesson);
      if (onSuccess) onSuccess();
    } catch (err) {
      setError('Failed to fetch lesson details');
    } finally {
      setLoading(false);
    }
  }, []);

  const showSuccess = useCallback((message) => {
    setSuccess(message);
    setTimeout(() => setSuccess(null), 5000);
  }, []);

  const showError = useCallback((message) => {
    setError(message);
    setTimeout(() => setError(null), 8000);
  }, []);

  const clearMessages = useCallback(() => {
    setError(null);
    setSuccess(null);
  }, []);

  useEffect(() => {
    fetchCourses();
    checkApiStatus();
    const interval = setInterval(checkApiStatus, API_STATUS_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchCourses, checkApiStatus]);

  return {
    courses,
    selectedCourse,
    selectedLesson,
    questions,
    loading,
    error,
    success,
    apiStatus,
    setSelectedCourse,
    setSelectedLesson,
    setQuestions,
    fetchCourses,
    fetchQuestions,
    handleSelectCourse,
    handleSelectLesson,
    showSuccess,
    showError,
    clearMessages,
  };
}
