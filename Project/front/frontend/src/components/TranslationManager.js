import React, { useState, useEffect } from 'react';
import './TranslationManager.css';

const TranslationManager = () => {
  const [languages, setLanguages] = useState({});
  const [targetLanguage, setTargetLanguage] = useState('sr');
  const [courses, setCourses] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [translateMode, setTranslateMode] = useState('course'); // course | questions | lessons | learning-objects
  const [translating, setTranslating] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    fetchLanguages();
    fetchCourses();
  }, []);

  const fetchLanguages = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/translate/languages');
      const data = await response.json();
      if (data.success) {
        setLanguages(data.languages);
      }
    } catch (error) {
      console.error('Error fetching languages:', error);
    }
  };

  const fetchCourses = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/courses');
      const data = await response.json();
      if (data.courses) {
        setCourses(data.courses);
        if (data.courses.length > 0) {
          setSelectedCourse(data.courses[0].id);
        }
      }
    } catch (error) {
      console.error('Error fetching courses:', error);
    }
  };

  const showMessage = (msg, isError = false) => {
    setMessage({ text: msg, isError });
    setTimeout(() => setMessage(null), 5000);
  };

  const handleTranslate = async () => {
    if (!selectedCourse || !targetLanguage) {
      showMessage('Please select a course and language', true);
      return;
    }

    setTranslating(true);
    try {
      let response;
      
      if (translateMode === 'course') {
        response = await fetch(`http://localhost:5000/api/translate/course/${selectedCourse}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ target_language: targetLanguage })
        });
      } else {
        showMessage('Individual translation modes coming soon', true);
        return;
      }

      const data = await response.json();
      if (data.success) {
        showMessage(`Translation complete! ${languages[targetLanguage]} translation created.`);
      } else {
        showMessage(data.error || 'Translation failed', true);
      }
    } catch (error) {
      showMessage('Translation error: ' + error.message, true);
      console.error(error);
    } finally {
      setTranslating(false);
    }
  };

  return (
    <div className="translation-manager">
      <div className="tm-container">
        <div className="tm-header">
          <h1>Translate Content</h1>
          <p className="subtitle">Translate your entire course or specific content types to different languages</p>
        </div>

        {/* Message Display */}
        {message && (
          <div className={`message ${message.isError ? 'error' : 'success'}`}>
            {message.text}
          </div>
        )}

        {/* Translation Mode Selection */}
        <div className="tm-section">
          <h3>What do you want to translate?</h3>
          <div className="mode-buttons">
            <button
              className={`mode-btn ${translateMode === 'course' ? 'active' : ''}`}
              onClick={() => setTranslateMode('course')}
            >
              Entire Course
            </button>
            <button
              className={`mode-btn ${translateMode === 'questions' ? 'active' : ''}`}
              onClick={() => setTranslateMode('questions')}
              title="Translate all questions"
            >
              All Questions
            </button>
            <button
              className={`mode-btn ${translateMode === 'lessons' ? 'active' : ''}`}
              onClick={() => setTranslateMode('lessons')}
              title="Translate all lessons"
            >
              All Lessons
            </button>
            <button
              className={`mode-btn ${translateMode === 'learning-objects' ? 'active' : ''}`}
              onClick={() => setTranslateMode('learning-objects')}
              title="Translate all learning objects"
            >
              All Learning Objects
            </button>
          </div>
        </div>

        {/* Configuration Form */}
        <div className="tm-section">
          <div className="form-grid">
            <div className="form-group">
              <label>Select Course:</label>
              <select value={selectedCourse || ''} onChange={(e) => setSelectedCourse(parseInt(e.target.value))}>
                <option value="">-- Select a course --</option>
                {courses.map((course) => (
                  <option key={course.id} value={course.id}>
                    {course.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Target Language:</label>
              <select value={targetLanguage} onChange={(e) => setTargetLanguage(e.target.value)}>
                {Object.entries(languages).map(([code, name]) => (
                  <option key={code} value={code}>
                    {name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Translate Button */}
        <div className="tm-section">
          <button
            className="btn-translate-large"
            onClick={handleTranslate}
            disabled={translating || !selectedCourse}
          >
            {translating ? 'Translating...' : 'Start Translation'}
          </button>
        </div>

        {/* Info Message */}
        <div className="info-box">
          <p><strong>Tip:</strong> Translations use your local Ollama model (qwen2.5:14b). This may take a few minutes depending on content size.</p>
        </div>
      </div>
    </div>
  );
};

export default TranslationManager;
