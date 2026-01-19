import React, { useState, useEffect } from 'react';
import './TranslationManager.css';

const TranslationManager = () => {
  const [languages, setLanguages] = useState({});
  const [targetLanguage, setTargetLanguage] = useState('en');
  const [quizzes, setQuizzes] = useState([]);
  const [selectedQuizzes, setSelectedQuizzes] = useState([]);
  const [translating, setTranslating] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0, currentQuiz: '' });
  const [message, setMessage] = useState(null);
  const [translationResults, setTranslationResults] = useState([]);

  useEffect(() => {
    fetchLanguages();
    fetchQuizzes();
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

  const fetchQuizzes = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/quizzes');
      const data = await response.json();
      if (data.quizzes) {
        setQuizzes(data.quizzes);
      }
    } catch (error) {
      console.error('Error fetching quizzes:', error);
    }
  };

  const showMessage = (msg, isError = false) => {
    setMessage({ text: msg, isError });
    setTimeout(() => setMessage(null), 8000);
  };

  const toggleQuizSelection = (quizId) => {
    setSelectedQuizzes(prev => 
      prev.includes(quizId) 
        ? prev.filter(id => id !== quizId)
        : [...prev, quizId]
    );
  };

  const selectAllQuizzes = () => {
    if (selectedQuizzes.length === quizzes.length) {
      setSelectedQuizzes([]);
    } else {
      setSelectedQuizzes(quizzes.map(q => q.id));
    }
  };

  const handleTranslate = async () => {
    if (selectedQuizzes.length === 0) {
      showMessage('Please select at least one quiz to translate', true);
      return;
    }

    if (!targetLanguage) {
      showMessage('Please select a target language', true);
      return;
    }

    setTranslating(true);
    setTranslationResults([]);
    setProgress({ current: 0, total: selectedQuizzes.length, currentQuiz: '' });

    const results = [];

    for (let i = 0; i < selectedQuizzes.length; i++) {
      const quizId = selectedQuizzes[i];
      const quiz = quizzes.find(q => q.id === quizId);
      
      setProgress({ 
        current: i + 1, 
        total: selectedQuizzes.length, 
        currentQuiz: quiz?.title || `Quiz #${quizId}` 
      });

      try {
        const response = await fetch(`http://localhost:5000/api/translate/quiz/${quizId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ target_language: targetLanguage })
        });

        const data = await response.json();
        
        results.push({
          quizId,
          quizTitle: quiz?.title || `Quiz #${quizId}`,
          success: data.success,
          questionsTranslated: data.questions_translated || 0,
          error: data.error
        });

      } catch (error) {
        results.push({
          quizId,
          quizTitle: quiz?.title || `Quiz #${quizId}`,
          success: false,
          error: error.message
        });
      }
    }

    setTranslationResults(results);
    setTranslating(false);
    
    const successCount = results.filter(r => r.success).length;
    const totalQuestions = results.reduce((sum, r) => sum + (r.questionsTranslated || 0), 0);
    
    if (successCount === results.length) {
      showMessage(`✓ All ${successCount} quizzes translated! (${totalQuestions} questions total)`);
    } else {
      showMessage(`Translated ${successCount}/${results.length} quizzes. Some failed.`, true);
    }
  };

  const getQuizTranslationStatus = (quiz) => {
    // Check if quiz has any translated questions
    if (quiz.available_languages && quiz.available_languages.length > 0) {
      return quiz.available_languages;
    }
    return [];
  };

  return (
    <div className="translation-manager">
      <div className="tm-container">
        <div className="tm-header">
          <h1>🌐 Quiz Translation</h1>
          <p className="subtitle">Translate your quizzes so students can take them in different languages</p>
        </div>

        {/* Message Display */}
        {message && (
          <div className={`message ${message.isError ? 'error' : 'success'}`}>
            {message.text}
          </div>
        )}

        {/* Progress Bar */}
        {translating && (
          <div className="translation-progress">
            <div className="progress-header">
              <span>Translating: {progress.currentQuiz}</span>
              <span>{progress.current} / {progress.total}</span>
            </div>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${(progress.current / progress.total) * 100}%` }}
              />
            </div>
          </div>
        )}

        {/* Language Selection */}
        <div className="tm-section">
          <h3>Select Target Language</h3>
          <div className="language-grid">
            {Object.entries(languages).map(([code, name]) => (
              <button
                key={code}
                className={`language-btn ${targetLanguage === code ? 'active' : ''}`}
                onClick={() => setTargetLanguage(code)}
                disabled={translating}
              >
                <span className="lang-flag">{getLanguageFlag(code)}</span>
                <span className="lang-name">{name}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Quiz Selection */}
        <div className="tm-section">
          <div className="section-header">
            <h3>Select Quizzes to Translate</h3>
            <button 
              className="btn-select-all"
              onClick={selectAllQuizzes}
              disabled={translating || quizzes.length === 0}
            >
              {selectedQuizzes.length === quizzes.length ? 'Deselect All' : 'Select All'}
            </button>
          </div>

          {quizzes.length === 0 ? (
            <div className="empty-state">
              <p>No quizzes found. Create some quizzes first!</p>
            </div>
          ) : (
            <div className="quiz-grid">
              {quizzes.map(quiz => (
                <div 
                  key={quiz.id}
                  className={`quiz-card ${selectedQuizzes.includes(quiz.id) ? 'selected' : ''}`}
                  onClick={() => !translating && toggleQuizSelection(quiz.id)}
                >
                  <div className="quiz-checkbox">
                    <input 
                      type="checkbox" 
                      checked={selectedQuizzes.includes(quiz.id)}
                      onChange={() => {}}
                      disabled={translating}
                    />
                  </div>
                  <div className="quiz-info">
                    <h4>{quiz.title}</h4>
                    <div className="quiz-meta">
                      <span className="meta-item">📝 {quiz.question_count} questions</span>
                    </div>
                    {quiz.available_languages && quiz.available_languages.length > 0 && (
                      <div className="translated-langs">
                        <span className="langs-label">Translated:</span>
                        {quiz.available_languages.map(lang => (
                          <span key={lang} className="lang-tag">{getLanguageFlag(lang)} {lang.toUpperCase()}</span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Translate Button */}
        <div className="tm-section">
          <button
            className="btn-translate-large"
            onClick={handleTranslate}
            disabled={translating || selectedQuizzes.length === 0}
          >
            {translating 
              ? `Translating... (${progress.current}/${progress.total})`
              : `Translate ${selectedQuizzes.length} Quiz${selectedQuizzes.length !== 1 ? 'zes' : ''} to ${languages[targetLanguage] || targetLanguage}`
            }
          </button>
        </div>

        {/* Translation Results */}
        {translationResults.length > 0 && (
          <div className="tm-section results-section">
            <h3>Translation Results</h3>
            <div className="results-list">
              {translationResults.map((result, idx) => (
                <div key={idx} className={`result-item ${result.success ? 'success' : 'error'}`}>
                  <span className="result-icon">{result.success ? '✓' : '✗'}</span>
                  <span className="result-title">{result.quizTitle}</span>
                  {result.success ? (
                    <span className="result-detail">{result.questionsTranslated} questions translated</span>
                  ) : (
                    <span className="result-error">{result.error}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Info Message */}
        <div className="info-box">
          <p><strong>💡 How it works:</strong></p>
          <ul>
            <li>Select the quizzes you want to translate</li>
            <li>Choose the target language</li>
            <li>Click translate - each question will be translated using AI</li>
            <li>When students take the quiz, they can choose their language!</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

// Helper function to get flag emoji for language code
const getLanguageFlag = (code) => {
  const flags = {
    'en': '🇬🇧',
    'sr': '🇷🇸',
    'fr': '🇫🇷',
    'es': '🇪🇸',
    'de': '🇩🇪',
    'ru': '🇷🇺',
    'zh': '🇨🇳',
    'ja': '🇯🇵',
    'pt': '🇵🇹',
    'it': '🇮🇹'
  };
  return flags[code] || '🌐';
};

export default TranslationManager;
