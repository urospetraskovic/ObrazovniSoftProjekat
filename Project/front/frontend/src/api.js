/**
 * API Client Module
 * Centralized API calls for all backend endpoints
 * Eliminates scattered axios calls throughout the application
 */

import axios from 'axios';

const API_URL = 'http://localhost:5000/api';

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ==================== COURSE ENDPOINTS ====================

export const courseApi = {
  getAll: () => apiClient.get('/courses'),
  getById: (courseId) => apiClient.get(`/courses/${courseId}`),
  create: (courseData) => apiClient.post('/courses', courseData),
  update: (courseId, courseData) => apiClient.put(`/courses/${courseId}`, courseData),
  delete: (courseId) => apiClient.delete(`/courses/${courseId}`),
};

// ==================== LESSON ENDPOINTS ====================

export const lessonApi = {
  getForCourse: (courseId) => apiClient.get(`/courses/${courseId}/lessons`),
  getById: (lessonId) => apiClient.get(`/lessons/${lessonId}`),
  create: (courseId, formData) => apiClient.post(`/courses/${courseId}/lessons`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  delete: (lessonId) => apiClient.delete(`/lessons/${lessonId}`),
  parse: (lessonId) => apiClient.post(`/lessons/${lessonId}/parse`),
  getSections: (lessonId) => apiClient.get(`/lessons/${lessonId}/sections`),
  getOntology: (lessonId) => apiClient.get(`/lessons/${lessonId}/ontology`),
  clearOntology: (lessonId) => apiClient.post(`/lessons/${lessonId}/ontology/clear`),
  generateOntology: (lessonId) => apiClient.post(`/lessons/${lessonId}/ontology/generate`),
};

// ==================== SECTION ENDPOINTS ====================

export const sectionApi = {
  getForLesson: (lessonId) => apiClient.get(`/lessons/${lessonId}/sections`),
  getById: (sectionId) => apiClient.get(`/sections/${sectionId}`),
  create: (lessonId, sectionData) => apiClient.post(`/lessons/${lessonId}/sections`, sectionData),
  update: (sectionId, sectionData) => apiClient.put(`/sections/${sectionId}`, sectionData),
  delete: (sectionId) => apiClient.delete(`/sections/${sectionId}`),
};

// ==================== LEARNING OBJECT ENDPOINTS ====================

export const learningObjectApi = {
  getForSection: (sectionId) => apiClient.get(`/sections/${sectionId}/learning-objects`),
  getById: (loId) => apiClient.get(`/learning-objects/${loId}`),
  create: (sectionId, loData) => apiClient.post(`/sections/${sectionId}/learning-objects`, loData),
  update: (loId, loData) => apiClient.put(`/learning-objects/${loId}`, loData),
  delete: (loId) => apiClient.delete(`/learning-objects/${loId}`),
};

// ==================== QUESTION ENDPOINTS ====================

export const questionApi = {
  getAll: (courseId = null) => {
    const params = courseId ? `?course_id=${courseId}` : '';
    return apiClient.get(`/questions${params}`);
  },
  getById: (questionId) => apiClient.get(`/questions/${questionId}`),
  create: (questionData) => apiClient.post('/questions', questionData),
  generate: (generationParams) => apiClient.post('/generate-questions', generationParams),
  delete: (questionId) => apiClient.delete(`/questions/${questionId}`),
};

// ==================== QUIZ ENDPOINTS ====================

export const quizApi = {
  getForCourse: (courseId) => apiClient.get(`/courses/${courseId}/quizzes`),
  getById: (quizId) => apiClient.get(`/quizzes/${quizId}`),
  create: (quizData) => apiClient.post('/quizzes', quizData),
  update: (quizId, quizData) => apiClient.put(`/quizzes/${quizId}`, quizData),
  delete: (quizId) => apiClient.delete(`/quizzes/${quizId}`),
  addQuestions: (quizId, questionIds) => apiClient.post(
    `/quizzes/${quizId}/questions`,
    { question_ids: questionIds }
  ),
  removeQuestion: (quizId, questionId) => apiClient.delete(
    `/quizzes/${quizId}/questions/${questionId}`
  ),
};

// ==================== HEALTH CHECK ====================

export const healthApi = {
  check: () => apiClient.get('/health'),
};

// ==================== ONTOLOGY ENDPOINTS ====================

export const ontologyApi = {
  getStats: () => apiClient.get('/ontology/stats'),
  exportFull: (format = 'json') => apiClient.get(`/ontology/export?format=${format}`),
  exportCourse: (courseId) => apiClient.get(`/ontology/export/course/${courseId}`, {
    responseType: 'blob'
  }),
  exportLesson: (lessonId) => apiClient.get(`/ontology/export/lesson/${lessonId}`, {
    responseType: 'blob'
  }),
  save: (courseId = null) => apiClient.post('/ontology/save', { course_id: courseId }),
};

// ==================== CHATBOT ENDPOINTS ====================

export const chatApi = {
  sendMessage: (message, courseId, lessonId, conversationHistory) => 
    apiClient.post('/chat', {
      message,
      course_id: courseId,
      lesson_id: lessonId,
      conversation_history: conversationHistory
    }),
  explainAnswer: (question, correctAnswer, userAnswer) =>
    apiClient.post('/chat/explain-answer', {
      question,
      correct_answer: correctAnswer,
      user_answer: userAnswer
    })
};

// ==================== ERROR HANDLING ====================

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 500) {
      console.error('[API ERROR]', error.response.data?.error || 'Server error');
    }
    return Promise.reject(error);
  }
);

export default apiClient;
