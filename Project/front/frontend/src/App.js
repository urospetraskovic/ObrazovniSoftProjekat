import React, { useState, useEffect, useCallback } from 'react';
import './App.css';

// API Client
import { courseApi, lessonApi, questionApi, healthApi } from './api';

// New components for course/lesson workflow
import CourseManager from './components/CourseManager';
import LessonManager from './components/LessonManager';
import ContentViewer from './components/ContentViewer';
import QuestionGenerator from './components/QuestionGenerator';
import QuestionBank from './components/QuestionBank';
import ManualQuestionAdder from './components/ManualQuestionAdder';
import QuizBuilder from './components/QuizBuilder';
import QuizSolver from './components/QuizSolver';

function App() {
  // Navigation state
  const [activeTab, setActiveTab] = useState('courses');
  
  // Data state
  const [courses, setCourses] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [selectedLesson, setSelectedLesson] = useState(null);
  const [questions, setQuestions] = useState([]);
  
  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [apiStatus, setApiStatus] = useState(null);

  // Fetch courses on mount and check API status
  useEffect(() => {
    fetchCourses();
    checkApiStatus();
    // Check API status every 30 seconds
    const interval = setInterval(checkApiStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const checkApiStatus = async () => {
    try {
      const response = await healthApi.check();
      setApiStatus(response.data);
    } catch (err) {
      // Silent failure for API status check
    }
  };

  const fetchCourses = async () => {
    try {
      setLoading(true);
      const response = await courseApi.getAll();
      setCourses(response.data.courses || []);
    } catch (err) {
      setError('Failed to fetch courses');
    } finally {
      setLoading(false);
    }
  };

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

  // When a course is selected, fetch its details
  const handleSelectCourse = async (course) => {
    try {
      setLoading(true);
      const response = await courseApi.getById(course.id);
      setSelectedCourse(response.data.course);
      setSelectedLesson(null);
      setActiveTab('lessons');
      await fetchQuestions(course.id);
    } catch (err) {
      setError('Failed to fetch course details');
    } finally {
      setLoading(false);
    }
  };

  // When a lesson is selected
  const handleSelectLesson = async (lesson) => {
    try {
      setLoading(true);
      const response = await lessonApi.getById(lesson.id);
      setSelectedLesson(response.data.lesson);
      setActiveTab('content');
    } catch (err) {
      setError('Failed to fetch lesson details');
    } finally {
      setLoading(false);
    }
  };

  const clearMessages = () => {
    setError(null);
    setSuccess(null);
  };

  const showSuccess = (message) => {
    setSuccess(message);
    setTimeout(() => setSuccess(null), 5000);
  };

  const showError = (message) => {
    setError(message);
    setTimeout(() => setError(null), 8000);
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'courses':
        return (
          <CourseManager
            courses={courses}
            onSelectCourse={handleSelectCourse}
            onCoursesChange={fetchCourses}
            onSuccess={showSuccess}
            onError={showError}
            loading={loading}
          />
        );
      
      case 'lessons':
        return selectedCourse ? (
          <LessonManager
            course={selectedCourse}
            onSelectLesson={handleSelectLesson}
            onLessonsChange={() => handleSelectCourse(selectedCourse)}
            onSuccess={showSuccess}
            onError={showError}
            onBack={() => {
              setSelectedCourse(null);
              setActiveTab('courses');
            }}
            loading={loading}
          />
        ) : (
          <div className="card">
            <p>Please select a course first</p>
            <button className="btn-primary" onClick={() => setActiveTab('courses')}>
              Go to Courses
            </button>
          </div>
        );
      
      case 'content':
        return selectedLesson ? (
          <ContentViewer
            lesson={selectedLesson}
            onBack={() => setActiveTab('lessons')}
            onSuccess={showSuccess}
            onError={showError}
            onLessonUpdate={(updatedLesson) => setSelectedLesson(updatedLesson)}
          />
        ) : (
          <div className="card">
            <p>Please select a lesson first</p>
            <button className="btn-primary" onClick={() => setActiveTab('lessons')}>
              Go to Lessons
            </button>
          </div>
        );
      
      case 'generate':
        return selectedCourse ? (
          <QuestionGenerator
            course={selectedCourse}
            onQuestionsGenerated={(newQuestions) => {
              setQuestions([...questions, ...newQuestions]);
              showSuccess(`Generated ${newQuestions.length} questions!`);
            }}
            onSuccess={showSuccess}
            onError={showError}
            loading={loading}
          />
        ) : (
          <div className="card">
            <p>Please select a course first to generate questions</p>
            <button className="btn-primary" onClick={() => setActiveTab('courses')}>
              Go to Courses
            </button>
          </div>
        );
      
      case 'questions':
        return (
          <div className="questions-section">
            {/* Manual Question Adder */}
            {selectedCourse && (
              <ManualQuestionAdder
                courseId={selectedCourse.id}
                lessons={selectedCourse.lessons || []}
                onSuccess={showSuccess}
                onError={showError}
                onRefresh={() => fetchQuestions(selectedCourse?.id)}
              />
            )}
            
            {/* Question Bank */}
            <QuestionBank
              questions={questions}
              courseId={selectedCourse?.id}
              onRefresh={() => fetchQuestions(selectedCourse?.id)}
              onSuccess={showSuccess}
              onError={showError}
            />
          </div>
        );
      
      case 'quizzes':
        return (
          <QuizBuilder
            questions={questions}
            course={selectedCourse}
            onSuccess={showSuccess}
            onError={showError}
          />
        );
      
      case 'solve':
        return selectedCourse ? (
          <QuizSolver
            courseId={selectedCourse.id}
            onBack={() => setActiveTab('quizzes')}
            onSuccess={showSuccess}
            onError={showError}
          />
        ) : (
          <div className="card">
            <p>Please select a course first to take quizzes</p>
            <button className="btn-primary" onClick={() => setActiveTab('courses')}>
              Go to Courses
            </button>
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <div className="app">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <h1>🎓 SOLO Quiz</h1>
          <p>Question Generator</p>
        </div>

        <nav className="sidebar-nav">
          {/* Main Workflow */}
          <div className="nav-section">
            <div className="nav-section-title">Workflow</div>
            <button
              className={`nav-link ${activeTab === 'courses' ? 'active' : ''}`}
              onClick={() => { setActiveTab('courses'); clearMessages(); }}
            >
              <span>📚</span>
              Courses
            </button>
            <button
              className={`nav-link ${activeTab === 'lessons' ? 'active' : ''}`}
              onClick={() => { setActiveTab('lessons'); clearMessages(); }}
              disabled={!selectedCourse}
            >
              <span>📖</span>
              Lessons
            </button>
            <button
              className={`nav-link ${activeTab === 'content' ? 'active' : ''}`}
              onClick={() => { setActiveTab('content'); clearMessages(); }}
              disabled={!selectedLesson}
            >
              <span>📄</span>
              Content
            </button>
          </div>

          {/* Question Management */}
          <div className="nav-section">
            <div className="nav-section-title">Questions</div>
            <button
              className={`nav-link ${activeTab === 'generate' ? 'active' : ''}`}
              onClick={() => { setActiveTab('generate'); clearMessages(); }}
              disabled={!selectedCourse}
            >
              <span>⚡</span>
              Generate
            </button>
            <button
              className={`nav-link ${activeTab === 'questions' ? 'active' : ''}`}
              onClick={() => { setActiveTab('questions'); clearMessages(); fetchQuestions(selectedCourse?.id); }}
            >
              <span>❓</span>
              Bank
            </button>
            <button
              className={`nav-link ${activeTab === 'quizzes' ? 'active' : ''}`}
              onClick={() => { setActiveTab('quizzes'); clearMessages(); }}
            >
              <span>📝</span>
              Build Quiz
            </button>
            <button
              className={`nav-link ${activeTab === 'solve' ? 'active' : ''}`}
              onClick={() => { setActiveTab('solve'); clearMessages(); }}
              disabled={!selectedCourse}
            >
              <span>✅</span>
              Take Quiz
            </button>
          </div>
        </nav>

        <div className="sidebar-footer">
          {selectedCourse && (
            <div style={{ fontSize: '0.9rem', color: 'var(--neutral-700)', lineHeight: '1.4' }}>
              <strong style={{ display: 'block', color: 'var(--neutral-800)', marginBottom: '4px' }}>Selected</strong>
              <span style={{ fontSize: '0.85rem' }}>📚 {selectedCourse.name}</span>
              {selectedLesson && (
                <span style={{ display: 'block', fontSize: '0.85rem', marginTop: '4px' }}>📖 {selectedLesson.title}</span>
              )}
            </div>
          )}
        </div>
      </aside>

      {/* Main Container */}
      <div className="main-container">
        {/* Top Bar */}
        <div className="top-bar">
          <div className="breadcrumb-container">
            {selectedCourse ? (
              <>
                <strong>📚 {selectedCourse.name}</strong>
                {selectedLesson && (
                  <>
                    <span>/</span>
                    <strong>📖 {selectedLesson.title}</strong>
                  </>
                )}
              </>
            ) : (
              <strong>Welcome to SOLO Quiz Generator</strong>
            )}
          </div>
          <div className="top-bar-actions">
            {apiStatus?.api_exhausted && (
              <div style={{ color: '#dc2626', fontSize: '0.85rem', fontWeight: '600' }}>
                ⚠️ API Keys Exhausted
              </div>
            )}
          </div>
        </div>

        {/* Main Content Area */}
        <main className="main-content">
          <div className="container">
            {/* Alert Messages */}
            {apiStatus?.api_exhausted && (
              <div className="alert alert-error">
                <div className="alert-icon">⚠️</div>
                <div className="alert-content">
                  <strong>API Keys Exhausted!</strong>
                  <p>All OpenRouter and GitHub Models keys have hit their daily limits. Please come back tomorrow or check your API quotas.</p>
                </div>
              </div>
            )}
            {error && (
              <div className="alert alert-error">
                <div className="alert-icon">❌</div>
                <div className="alert-content">
                  <strong>Error</strong>
                  <p>{error}</p>
                </div>
              </div>
            )}
            {success && (
              <div className="alert alert-success">
                <div className="alert-icon">✅</div>
                <div className="alert-content">
                  <strong>Success</strong>
                  <p>{success}</p>
                </div>
              </div>
            )}

            {/* Page Content */}
            {renderContent()}

            {/* Info Section - only on courses page */}
            {activeTab === 'courses' && (
              <div className="info-card" style={{ marginTop: '40px' }}>
                <h3>📋 How It Works</h3>
                <ol>
                  <li><strong>Create Course:</strong> Start by creating a course (e.g., "Operating Systems")</li>
                  <li><strong>Upload Lessons:</strong> Add PDF lessons to your course</li>
                  <li><strong>Parse Content:</strong> AI extracts sections and learning objects from lessons</li>
                  <li><strong>Generate Questions:</strong> Create SOLO-based questions from your content</li>
                  <li><strong>Build Quiz:</strong> Combine questions into quizzes and download as JSON</li>
                </ol>
                <div className="solo-levels">
                  <h4>📚 SOLO Taxonomy Levels:</h4>
                  <ul>
                    <li><strong>Unistructural:</strong> Single fact recall (from lesson)</li>
                    <li><strong>Multistructural:</strong> Multiple related facts (from sections)</li>
                    <li><strong>Relational:</strong> Analyze relationships (from learning objects)</li>
                    <li><strong>Extended Abstract:</strong> Combine knowledge (from 2+ lessons)</li>
                  </ul>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
