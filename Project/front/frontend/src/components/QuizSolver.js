import React, { useState, useEffect, useCallback } from 'react';
import { quizApi } from '../api';

function QuizSolver({ courseId, onBack, onSuccess, onError }) {
  const [quizzes, setQuizzes] = useState([]);
  const [selectedQuiz, setSelectedQuiz] = useState(null);
  const [quizData, setQuizData] = useState(null);
  const [userAnswers, setUserAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const [score, setScore] = useState(null);
  const [loading, setLoading] = useState(false);
  const [timeElapsed, setTimeElapsed] = useState(0);
  const [revealedAnswers, setRevealedAnswers] = useState({});

  const fetchQuizzes = useCallback(async () => {
    try {
      setLoading(true);
      const response = await quizApi.getForCourse(courseId);
      setQuizzes(response.data.quizzes || []);
    } catch (err) {
      onError('Failed to fetch quizzes');
    } finally {
      setLoading(false);
    }
  }, [courseId, onError]);

  useEffect(() => {
    fetchQuizzes();
  }, [fetchQuizzes]);

  // Timer effect - starts when quiz is selected
  useEffect(() => {
    let interval;
    if (quizData && !submitted) {
      interval = setInterval(() => {
        setTimeElapsed(prev => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [quizData, submitted]);

  const handleSelectQuiz = async (quiz) => {
    try {
      setLoading(true);
      const response = await quizApi.getById(quiz.id);
      setQuizData(response.data.quiz);
      setSelectedQuiz(quiz);
      setUserAnswers({});
      setSubmitted(false);
      setScore(null);
    } catch (err) {
      onError('Failed to load quiz');
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerChange = (questionId, answer) => {
    setUserAnswers({
      ...userAnswers,
      [questionId]: answer
    });
  };

  const calculateScore = () => {
    if (!quizData?.questions) return 0;
    
    let correctCount = 0;
    quizData.questions.forEach(question => {
      const userAnswer = userAnswers[question.id];
      if (userAnswer !== undefined) {
        if (question.correct_option_index !== undefined) {
          // Multiple choice
          if (parseInt(userAnswer) === question.correct_option_index) {
            correctCount++;
          }
        } else if (question.correct_answer) {
          // True/False or short answer
          if (userAnswer.toLowerCase() === question.correct_answer.toLowerCase()) {
            correctCount++;
          }
        }
      }
    });

    const percentage = (correctCount / quizData.questions.length) * 100;
    return { correctCount, totalCount: quizData.questions.length, percentage };
  };

  const handleSubmit = () => {
    const scoreData = calculateScore();
    setScore(scoreData);
    setSubmitted(true);
    onSuccess(`Quiz submitted! Score: ${scoreData.correctCount}/${scoreData.totalCount} (${scoreData.percentage.toFixed(1)}%)`);
  };

  const handleRetake = () => {
    setUserAnswers({});
    setSubmitted(false);
    setScore(null);
    setTimeElapsed(0);
    setRevealedAnswers({});
  };

  const toggleRevealAnswer = (questionId) => {
    setRevealedAnswers({
      ...revealedAnswers,
      [questionId]: !revealedAnswers[questionId]
    });
  };

  const formatTime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    }
    return `${minutes}:${String(secs).padStart(2, '0')}`;
  };

  const handleBackToList = () => {
    setSelectedQuiz(null);
    setQuizData(null);
    setUserAnswers({});
    setSubmitted(false);
    setScore(null);
    setTimeElapsed(0);
    setRevealedAnswers({});
  };

  // Quiz list view
  if (!selectedQuiz) {
    return (
      <div className="quiz-solver">
        <div className="card">
          <div className="card-header">
            <button className="btn-back" onClick={onBack}>← Back</button>
            <h2>📝 Available Quizzes</h2>
          </div>

          {loading ? (
            <div className="loading-state">Loading quizzes...</div>
          ) : quizzes.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">📭</div>
              <p>No quizzes available for this course</p>
              <p className="hint">Create a quiz using the "Build Quiz" section first</p>
            </div>
          ) : (
            <div className="quiz-list">
              {quizzes.map(quiz => (
                <div
                  key={quiz.id}
                  className="quiz-card"
                  onClick={() => handleSelectQuiz(quiz)}
                >
                  <div className="quiz-info">
                    <h3>{quiz.title}</h3>
                    {quiz.description && <p className="quiz-description">{quiz.description}</p>}
                  </div>
                  <div className="quiz-meta">
                    <div className="meta-item">
                      <span className="meta-icon">❓</span>
                      <span>{quiz.question_count} questions</span>
                    </div>
                    {quiz.time_limit_minutes && (
                      <div className="meta-item">
                        <span className="meta-icon">⏱️</span>
                        <span>{quiz.time_limit_minutes} min</span>
                      </div>
                    )}
                    {quiz.passing_score && (
                      <div className="meta-item">
                        <span className="meta-icon">✓</span>
                        <span>Pass: {quiz.passing_score}%</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Quiz taking view
  if (quizData) {
    return (
      <div className="quiz-taker">
        <div className="card">
          <div className="card-header">
            <div>
              <button className="btn-back" onClick={handleBackToList}>← Back to Quizzes</button>
              <h2>📝 {selectedQuiz.title}</h2>
              {selectedQuiz.description && (
                <p className="quiz-description">{selectedQuiz.description}</p>
              )}
            </div>
            {!submitted && (
              <div className="quiz-progress">
                <div className="progress-info">
                  <span>⏱️ Time: {formatTime(timeElapsed)}</span>
                  <span>Answered: {Object.keys(userAnswers).length}/{quizData.questions?.length || 0}</span>
                </div>
              </div>
            )}
          </div>

          {submitted && score ? (
            <div className="result-section">
              <div className="score-display">
                <div className="score-circle">
                  <span className="score-percentage">{score.percentage.toFixed(1)}%</span>
                </div>
                <div className="score-details">
                  <p>
                    <strong>Score:</strong> {score.correctCount} out of {score.totalCount} correct
                  </p>
                  <p>
                    <strong>Status:</strong>{' '}
                    {score.percentage >= (selectedQuiz.passing_score || 70) ? (
                      <span style={{ color: 'var(--success)' }}>✓ PASSED</span>
                    ) : (
                      <span style={{ color: 'var(--error)' }}>✗ FAILED</span>
                    )}
                  </p>
                </div>
              </div>
            </div>
          ) : null}

          <div className="questions-section">
            {quizData.questions?.map((question, index) => {
              const isCorrect =
                submitted &&
                ((question.correct_option_index !== undefined &&
                  parseInt(userAnswers[question.id]) === question.correct_option_index) ||
                  (question.correct_answer &&
                    userAnswers[question.id]?.toLowerCase() ===
                      question.correct_answer.toLowerCase()));

              return (
                <div
                  key={question.id}
                  className={`question-section ${submitted ? (isCorrect ? 'correct' : 'incorrect') : ''}`}
                >
                  <div className="question-header">
                    <h4>
                      Question {index + 1}
                      {submitted && (isCorrect ? ' ✓' : ' ✗')}
                    </h4>
                    <div className="question-meta">
                      <span className="solo-badge" style={{ backgroundColor: getSoloColor(question.solo_level) }}>
                        {question.solo_level.replace(/_/g, ' ')}
                      </span>
                    </div>
                  </div>

                  <p className="question-text">{question.question_text}</p>

                  {/* Lesson Source */}
                  <div className={`lesson-source ${question.solo_level === 'extended_abstract' ? 'extended-source' : ''}`}>
                    <span className="source-icon">📚</span>
                    {getLessonSourceDisplay(question)}
                  </div>

                  {question.question_type === 'multiple_choice' && question.options ? (
                    <div className="options-list">
                      {question.options.map((option, optIdx) => (
                        <label
                          key={optIdx}
                          className={`option-label ${
                            userAnswers[question.id] === optIdx.toString() ? 'selected' : ''
                          } ${submitted ? (optIdx === question.correct_option_index ? 'correct-answer' : '') : ''}`}
                        >
                          <input
                            type="radio"
                            name={`question-${question.id}`}
                            value={optIdx}
                            checked={userAnswers[question.id] === optIdx.toString()}
                            onChange={(e) => handleAnswerChange(question.id, e.target.value)}
                            disabled={submitted}
                          />
                          <span className="option-text">{option}</span>
                        </label>
                      ))}
                    </div>
                  ) : question.question_type === 'true_false' ? (
                    <div className="options-list">
                      {['True', 'False'].map((option, optIdx) => (
                        <label
                          key={optIdx}
                          className={`option-label ${
                            userAnswers[question.id] === option ? 'selected' : ''
                          } ${submitted ? (option === question.correct_answer ? 'correct-answer' : '') : ''}`}
                        >
                          <input
                            type="radio"
                            name={`question-${question.id}`}
                            value={option}
                            checked={userAnswers[question.id] === option}
                            onChange={(e) => handleAnswerChange(question.id, e.target.value)}
                            disabled={submitted}
                          />
                          <span className="option-text">{option}</span>
                        </label>
                      ))}
                    </div>
                  ) : (
                    <div className="short-answer">
                      <input
                        type="text"
                        placeholder="Enter your answer"
                        value={userAnswers[question.id] || ''}
                        onChange={(e) => handleAnswerChange(question.id, e.target.value)}
                        disabled={submitted}
                        className="answer-input"
                      />
                    </div>
                  )}

                  {!submitted && (
                    <button 
                      className="btn-show-answer"
                      onClick={() => toggleRevealAnswer(question.id)}
                    >
                      {revealedAnswers[question.id] ? '🙈 Hide Answer' : '👁️ Show Answer'}
                    </button>
                  )}

                  {revealedAnswers[question.id] && !submitted && (
                    <div className="revealed-answer">
                      <strong>Correct Answer:</strong>
                      {question.correct_option_index !== undefined && (
                        <p>{question.options[question.correct_option_index]}</p>
                      )}
                      {question.correct_answer && !question.options && (
                        <p>{question.correct_answer}</p>
                      )}
                      {question.explanation && (
                        <p className="answer-explanation">{question.explanation}</p>
                      )}
                    </div>
                  )}

                  {submitted && question.explanation && (
                    <div className="explanation">
                      <strong>Explanation:</strong> {question.explanation}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {!submitted ? (
            <div className="quiz-actions">
              <button className="btn-secondary" onClick={handleBackToList}>
                Cancel
              </button>
              <button
                className="btn-primary"
                onClick={handleSubmit}
                disabled={Object.keys(userAnswers).length === 0}
              >
                Submit Quiz
              </button>
            </div>
          ) : (
            <div className="quiz-actions">
              <button className="btn-secondary" onClick={handleBackToList}>
                Back to Quizzes
              </button>
              <button className="btn-primary" onClick={handleRetake}>
                Retake Quiz
              </button>
            </div>
          )}
        </div>
      </div>
    );
  }

  return null;
}

function getSoloColor(level) {
  const colors = {
    unistructural: '#8b5cf6',
    multistructural: '#ec4899',
    relational: '#f59e0b',
    extended_abstract: '#06b6d4'
  };
  return colors[level] || '#6b7280';
}

function getLessonSourceDisplay(question) {
  // Try to use lesson titles first
  if (question.secondary_lesson_title && question.primary_lesson_title) {
    return (
      <span className="source-text">
        From <strong>{question.primary_lesson_title}</strong> + <strong>{question.secondary_lesson_title}</strong>
      </span>
    );
  }
  
  if (question.primary_lesson_title) {
    return (
      <span className="source-text">
        From <strong>{question.primary_lesson_title}</strong>
      </span>
    );
  }
  
  // Fallback: extract from tags if titles are missing (for cross-topic questions)
  if (question.tags && question.tags.length > 0) {
    const lessonTags = question.tags.filter(tag => tag !== 'cross-topic');
    if (lessonTags.length > 1) {
      return (
        <span className="source-text">
          From <strong>{lessonTags[0]}</strong> + <strong>{lessonTags[1]}</strong>
        </span>
      );
    }
    if (lessonTags.length === 1) {
      return (
        <span className="source-text">
          From <strong>{lessonTags[0]}</strong>
        </span>
      );
    }
  }
  
  return null;
}

export default QuizSolver;
