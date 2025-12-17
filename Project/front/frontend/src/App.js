import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import './App.css';

// New components for course/lesson workflow
import CourseManager from './components/CourseManager';
import LessonManager from './components/LessonManager';
import ContentViewer from './components/ContentViewer';
import QuestionGenerator from './components/QuestionGenerator';
import QuestionBank from './components/QuestionBank';
import QuizBuilder from './components/QuizBuilder';

const API_URL = 'http://localhost:5000/api';

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
      const response = await axios.get(`${API_URL}/health`);
      setApiStatus(response.data);
    } catch (err) {
      console.error('Failed to check API status:', err);
    }
  };

  const fetchCourses = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/courses`);
      setCourses(response.data.courses || []);
    } catch (err) {
      setError('Failed to fetch courses');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchQuestions = useCallback(async (courseId = null) => {
    try {
      setLoading(true);
      const params = courseId ? `?course_id=${courseId}` : '';
      const response = await axios.get(`${API_URL}/questions${params}`);
      setQuestions(response.data.questions || []);
    } catch (err) {
      console.error('Failed to fetch questions:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // When a course is selected, fetch its details
  const handleSelectCourse = async (course) => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/courses/${course.id}`);
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
      const response = await axios.get(`${API_URL}/lessons/${lesson.id}`);
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
          <QuestionBank
            questions={questions}
            courseId={selectedCourse?.id}
            onRefresh={() => fetchQuestions(selectedCourse?.id)}
            onSuccess={showSuccess}
            onError={showError}
          />
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
      
      default:
        return null;
    }
  };

  return (
    <div className="app">
      <div className="container">
        {/* Header */}
        <div className="header">
          <h1>🎓 SOLO Quiz Generator</h1>
          <p>Course → Lesson → Section → Learning Objects → Questions</p>
        </div>

        {/* Navigation */}
        <nav className="nav-tabs">
          <button
            className={`nav-tab ${activeTab === 'courses' ? 'active' : ''}`}
            onClick={() => { setActiveTab('courses'); clearMessages(); }}
          >
            📚 Courses
          </button>
          <button
            className={`nav-tab ${activeTab === 'lessons' ? 'active' : ''}`}
            onClick={() => { setActiveTab('lessons'); clearMessages(); }}
            disabled={!selectedCourse}
          >
            📖 Lessons {selectedCourse && `(${selectedCourse.name})`}
          </button>
          <button
            className={`nav-tab ${activeTab === 'content' ? 'active' : ''}`}
            onClick={() => { setActiveTab('content'); clearMessages(); }}
            disabled={!selectedLesson}
          >
            📄 Content
          </button>
          <button
            className={`nav-tab ${activeTab === 'generate' ? 'active' : ''}`}
            onClick={() => { setActiveTab('generate'); clearMessages(); }}
            disabled={!selectedCourse}
          >
            ⚡ Generate Questions
          </button>
          <button
            className={`nav-tab ${activeTab === 'questions' ? 'active' : ''}`}
            onClick={() => { setActiveTab('questions'); clearMessages(); fetchQuestions(selectedCourse?.id); }}
          >
            ❓ Question Bank
          </button>
          <button
            className={`nav-tab ${activeTab === 'quizzes' ? 'active' : ''}`}
            onClick={() => { setActiveTab('quizzes'); clearMessages(); }}
          >
            📝 Build Quiz
          </button>
        </nav>

        {/* Breadcrumb */}
        <div className="breadcrumb">
          {selectedCourse && (
            <span>
              📚 {selectedCourse.name}
              {selectedLesson && ` → 📖 ${selectedLesson.title}`}
            </span>
          )}
        </div>

        {/* Messages */}
        {apiStatus?.api_exhausted && (
          <div className="error">
            ⚠️ <strong>API Keys Exhausted!</strong> All OpenRouter and GitHub Models keys have hit their daily limits. Please come back tomorrow or check your API quotas.
          </div>
        )}
        {error && <div className="error">{error}</div>}
        {success && <div className="success">{success}</div>}

        {/* Main Content */}
        <main className="main-content">
          {renderContent()}
        </main>

        {/* Footer info */}
        <div className="card info-card">
          <h3>📋 Workflow Guide</h3>
          <ol>
            <li><strong>Create Course:</strong> Start by creating a course (e.g., "Operating Systems")</li>
            <li><strong>Upload Lessons:</strong> Add PDF lessons to your course</li>
            <li><strong>Parse Content:</strong> AI extracts sections and learning objects from lessons</li>
            <li><strong>Generate Questions:</strong> Create SOLO-based questions from your content</li>
            <li><strong>Build Quiz:</strong> Combine questions into quizzes</li>
          </ol>
          <div className="solo-levels">
            <h4>SOLO Taxonomy Levels:</h4>
            <ul>
              <li><strong>Unistructural:</strong> Single fact recall (from lesson)</li>
              <li><strong>Multistructural:</strong> Multiple related facts (from sections)</li>
              <li><strong>Relational:</strong> Analyze relationships (from learning objects)</li>
              <li><strong>Extended Abstract:</strong> Combine knowledge (from 2 lessons)</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
