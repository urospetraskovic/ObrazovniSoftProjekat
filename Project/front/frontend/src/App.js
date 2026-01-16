import React, { useState, useEffect, useCallback } from 'react';
import './App.css';

// API Client
import { courseApi, lessonApi, questionApi, healthApi } from './api';

// Context
import { LanguageProvider, useLanguage } from './context/LanguageContext';

// New components for course/lesson workflow
import CourseManager from './components/CourseManager';
import LessonManager from './components/LessonManager';
import ContentViewer from './components/ContentViewer';
import QuestionGenerator from './components/QuestionGenerator';
import QuestionBank from './components/QuestionBank';
import ManualQuestionAdder from './components/ManualQuestionAdder';
import QuizBuilder from './components/QuizBuilder';
import QuizSolver from './components/QuizSolver';
import TranslationManager from './components/TranslationManager';
import SPARQLQueryTool from './components/SPARQLQueryTool';

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
      
      case 'translate':
        return (
          <TranslationManager />
        );
      
      case 'sparql':
        return (
          <SPARQLQueryTool />
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
          <h1>SOLO Quiz</h1>
          <p>Question Generator</p>
        </div>

        <nav className="sidebar-nav">
          {/* Main Workflow */}
          <div className="nav-section">
            <button
              className={`nav-link ${activeTab === 'courses' ? 'active' : ''}`}
              onClick={() => { setActiveTab('courses'); clearMessages(); }}
            >
              <span className="nav-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
              </span>
              Courses
            </button>
            <button
              className={`nav-link ${activeTab === 'lessons' ? 'active' : ''}`}
              onClick={() => { setActiveTab('lessons'); clearMessages(); }}
              disabled={!selectedCourse}
            >
              <span className="nav-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
              </span>
              Lessons
            </button>
            <button
              className={`nav-link ${activeTab === 'content' ? 'active' : ''}`}
              onClick={() => { setActiveTab('content'); clearMessages(); }}
              disabled={!selectedLesson}
            >
              <span className="nav-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
              </span>
              Content
            </button>
          </div>

          {/* Question Management */}
          <div className="nav-section">
            <div className="nav-section-title">Questions</div>
            <button
              className={`nav-link ${activeTab === 'generate' ? 'active' : ''}`}
              onClick={() => { setActiveTab('generate'); clearMessages(); }}
            >
              <span className="nav-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
              </span>
              Generate
            </button>
            <button
              className={`nav-link ${activeTab === 'questions' ? 'active' : ''}`}
              onClick={() => { setActiveTab('questions'); clearMessages(); fetchQuestions(selectedCourse?.id); }}
            >
              <span className="nav-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
              </span>
              Bank
            </button>
            <button
              className={`nav-link ${activeTab === 'quizzes' ? 'active' : ''}`}
              onClick={() => { setActiveTab('quizzes'); clearMessages(); }}
            >
              <span className="nav-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
              </span>
              Build Quiz
            </button>
            <button
              className={`nav-link ${activeTab === 'solve' ? 'active' : ''}`}
              onClick={() => { setActiveTab('solve'); clearMessages(); }}
            >
              <span className="nav-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
              </span>
              Take Quiz
            </button>
          </div>

          {/* Translation Management */}
          <div className="nav-section">
            <div className="nav-section-title">Content</div>
            <button
              className={`nav-link ${activeTab === 'translate' ? 'active' : ''}`}
              onClick={() => { setActiveTab('translate'); clearMessages(); }}
            >
              <span className="nav-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
              </span>
              Translate
            </button>
            <button
              className={`nav-link ${activeTab === 'sparql' ? 'active' : ''}`}
              onClick={() => { setActiveTab('sparql'); clearMessages(); }}
            >
              <span className="nav-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="1"/><path d="M12 1v6m0 6v6M4.22 4.22l4.24 4.24m5.08 5.08l4.24 4.24M1 12h6m6 0h6M4.22 19.78l4.24-4.24m5.08-5.08l4.24-4.24"/></svg>
              </span>
              SPARQL Query
            </button>
          </div>
        </nav>

        <div className="sidebar-footer">
          {selectedCourse && (
            <div className="selected-context">
              <strong>Current Selection</strong>
              <span className="context-item">{selectedCourse.name}</span>
              {selectedLesson && (
                <span className="context-item context-lesson">{selectedLesson.title}</span>
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
                <strong>{selectedCourse.name}</strong>
                {selectedLesson && (
                  <>
                    <span className="breadcrumb-separator">/</span>
                    <strong>{selectedLesson.title}</strong>
                  </>
                )}
              </>
            ) : (
              <strong>Welcome to SOLO Quiz Generator</strong>
            )}
          </div>
          <div className="top-bar-actions">
            {apiStatus?.api_exhausted && (
              <div className="api-warning">
                API Keys Exhausted
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
                <div className="alert-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                </div>
                <div className="alert-content">
                  <strong>API Keys Exhausted!</strong>
                  <p>All OpenRouter and GitHub Models keys have hit their daily limits. Please come back tomorrow or check your API quotas.</p>
                </div>
              </div>
            )}
            {error && (
              <div className="alert alert-error">
                <div className="alert-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
                </div>
                <div className="alert-content">
                  <strong>Error</strong>
                  <p>{error}</p>
                </div>
              </div>
            )}
            {success && (
              <div className="alert alert-success">
                <div className="alert-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                </div>
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
                <h3>How It Works</h3>
                <ol>
                  <li><strong>Create Course:</strong> Start by creating a course (e.g., "Operating Systems")</li>
                  <li><strong>Upload Lessons:</strong> Add PDF lessons to your course</li>
                  <li><strong>Parse Content:</strong> AI extracts sections and learning objects from lessons</li>
                  <li><strong>Generate Questions:</strong> Create SOLO-based questions from your content</li>
                  <li><strong>Build Quiz:</strong> Combine questions into quizzes and download as JSON</li>
                </ol>
                <div className="solo-levels">
                  <h4>SOLO Taxonomy Levels:</h4>
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

function AppWithLanguage() {
  return (
    <LanguageProvider>
      <AppContent />
    </LanguageProvider>
  );
}

function AppContent() {
  const { languages, selectedLanguage, setSelectedLanguage, loading: langsLoading } = useLanguage();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Get the App component instance
  const AppInstance = <App />;

  return (
    <div className="app-with-language">
      {/* Global Language Selector Header */}
      <div className="global-header">
        <div className="header-content">
          <div className="header-left">
            <h2>SOLO Quiz Generator</h2>
          </div>
          <div className="header-right">
            <div className="language-selector-global">
              <label>Language:</label>
              <select 
                value={selectedLanguage} 
                onChange={(e) => setSelectedLanguage(e.target.value)}
                disabled={langsLoading}
              >
                {Object.entries(languages).map(([code, name]) => (
                  <option key={code} value={code}>
                    {name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>
      
      {AppInstance}
    </div>
  );
}

export default AppWithLanguage;
