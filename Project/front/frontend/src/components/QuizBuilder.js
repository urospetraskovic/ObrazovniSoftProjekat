import React, { useState } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:5000/api';

function QuizBuilder({ questions, course, onSuccess, onError }) {
  const [quizTitle, setQuizTitle] = useState('');
  const [quizDescription, setQuizDescription] = useState('');
  const [selectedQuestionIds, setSelectedQuestionIds] = useState([]);
  const [filterLevel, setFilterLevel] = useState('all');
  const [timeLimit, setTimeLimit] = useState(null);
  const [creating, setCreating] = useState(false);
  const [createdQuiz, setCreatedQuiz] = useState(null);

  const filteredQuestions = questions.filter(q => 
    filterLevel === 'all' || q.solo_level === filterLevel
  );

  const handleToggleQuestion = (questionId) => {
    setSelectedQuestionIds(prev =>
      prev.includes(questionId)
        ? prev.filter(id => id !== questionId)
        : [...prev, questionId]
    );
  };

  const handleSelectAllFiltered = () => {
    const filteredIds = filteredQuestions.map(q => q.id);
    const allSelected = filteredIds.every(id => selectedQuestionIds.includes(id));
    
    if (allSelected) {
      setSelectedQuestionIds(prev => prev.filter(id => !filteredIds.includes(id)));
    } else {
      setSelectedQuestionIds(prev => [...new Set([...prev, ...filteredIds])]);
    }
  };

  const handleAutoSelect = (config) => {
    // Auto-select questions based on SOLO distribution
    const selected = [];
    const levels = ['unistructural', 'multistructural', 'relational', 'extended_abstract'];
    
    levels.forEach(level => {
      const levelQuestions = questions.filter(q => q.solo_level === level);
      const count = config[level] || 0;
      const shuffled = [...levelQuestions].sort(() => Math.random() - 0.5);
      selected.push(...shuffled.slice(0, count).map(q => q.id));
    });
    
    setSelectedQuestionIds(selected);
  };

  const handleCreateQuiz = async () => {
    if (!quizTitle.trim()) {
      onError('Please enter a quiz title');
      return;
    }
    
    if (selectedQuestionIds.length === 0) {
      onError('Please select at least one question');
      return;
    }

    try {
      setCreating(true);
      
      const response = await axios.post(`${API_URL}/quizzes`, {
        title: quizTitle,
        description: quizDescription,
        course_id: course?.id,
        question_ids: selectedQuestionIds,
        time_limit_minutes: timeLimit,
        shuffle_questions: true,
        shuffle_options: true
      });

      setCreatedQuiz(response.data.quiz);
      onSuccess(`Quiz "${quizTitle}" created with ${selectedQuestionIds.length} questions!`);
      
      // Reset form
      setQuizTitle('');
      setQuizDescription('');
      setSelectedQuestionIds([]);
      
    } catch (err) {
      onError(err.response?.data?.error || 'Failed to create quiz');
    } finally {
      setCreating(false);
    }
  };

  const handleExportQuiz = async (quizId) => {
    try {
      const response = await axios.get(`${API_URL}/quizzes/${quizId}/export`);
      onSuccess(`Quiz exported: ${response.data.filename}`);
    } catch (err) {
      onError('Failed to export quiz');
    }
  };

  const selectedQuestions = questions.filter(q => selectedQuestionIds.includes(q.id));
  const soloDistribution = {
    unistructural: selectedQuestions.filter(q => q.solo_level === 'unistructural').length,
    multistructural: selectedQuestions.filter(q => q.solo_level === 'multistructural').length,
    relational: selectedQuestions.filter(q => q.solo_level === 'relational').length,
    extended_abstract: selectedQuestions.filter(q => q.solo_level === 'extended_abstract').length
  };

  return (
    <div className="quiz-builder">
      <div className="card">
        <h2>📝 Build Quiz</h2>
        
        {/* Quiz Details */}
        <div className="quiz-details-section">
          <h3>Quiz Details</h3>
          <div className="form-group">
            <label>Quiz Title *</label>
            <input
              type="text"
              placeholder="e.g., Chapter 5 Review Quiz"
              value={quizTitle}
              onChange={(e) => setQuizTitle(e.target.value)}
            />
          </div>
          <div className="form-group">
            <label>Description</label>
            <textarea
              placeholder="Brief description of the quiz"
              value={quizDescription}
              onChange={(e) => setQuizDescription(e.target.value)}
              rows={2}
            />
          </div>
          <div className="form-group">
            <label>Time Limit (minutes, optional)</label>
            <input
              type="number"
              placeholder="No limit"
              value={timeLimit || ''}
              onChange={(e) => setTimeLimit(e.target.value ? parseInt(e.target.value) : null)}
              min="1"
            />
          </div>
        </div>

        {/* Quick Select */}
        <div className="quick-select-section">
          <h3>Quick Select</h3>
          <div className="quick-buttons">
            <button 
              className="btn-secondary"
              onClick={() => handleAutoSelect({ unistructural: 5, multistructural: 5, relational: 5, extended_abstract: 5 })}
            >
              Balanced (20 questions)
            </button>
            <button 
              className="btn-secondary"
              onClick={() => handleAutoSelect({ unistructural: 3, multistructural: 4, relational: 3 })}
            >
              Quick Quiz (10)
            </button>
            <button 
              className="btn-secondary"
              onClick={() => handleAutoSelect({ unistructural: 10, multistructural: 10, relational: 10, extended_abstract: 10 })}
            >
              Full Test (40)
            </button>
            <button 
              className="btn-secondary"
              onClick={() => setSelectedQuestionIds([])}
            >
              Clear All
            </button>
          </div>
        </div>

        {/* Question Selection */}
        <div className="question-selection-section">
          <h3>Select Questions ({selectedQuestionIds.length} selected)</h3>
          
          {/* Filter */}
          <div className="selection-filter">
            <select value={filterLevel} onChange={(e) => setFilterLevel(e.target.value)}>
              <option value="all">All Levels</option>
              <option value="unistructural">Unistructural</option>
              <option value="multistructural">Multistructural</option>
              <option value="relational">Relational</option>
              <option value="extended_abstract">Extended Abstract</option>
            </select>
            <button className="btn-secondary" onClick={handleSelectAllFiltered}>
              {filteredQuestions.every(q => selectedQuestionIds.includes(q.id)) 
                ? 'Deselect All Shown' 
                : 'Select All Shown'}
            </button>
          </div>

          {/* Questions List */}
          {questions.length === 0 ? (
            <div className="empty-state">
              <p>No questions available. Generate questions first.</p>
            </div>
          ) : (
            <div className="selectable-questions">
              {filteredQuestions.map((question) => (
                <div
                  key={question.id}
                  className={`selectable-question ${selectedQuestionIds.includes(question.id) ? 'selected' : ''}`}
                  onClick={() => handleToggleQuestion(question.id)}
                >
                  <div className="checkbox">
                    {selectedQuestionIds.includes(question.id) ? '✓' : ''}
                  </div>
                  <div className="question-preview">
                    <span className={`level-badge level-${question.solo_level}`}>
                      {question.solo_level?.replace('_', ' ')}
                    </span>
                    <p>{question.question_text?.substring(0, 100)}...</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Selection Summary */}
        {selectedQuestionIds.length > 0 && (
          <div className="selection-summary">
            <h4>Selection Summary</h4>
            <div className="summary-grid">
              <div className="summary-item">
                <span className="count">{soloDistribution.unistructural}</span>
                <span className="label">Unistructural</span>
              </div>
              <div className="summary-item">
                <span className="count">{soloDistribution.multistructural}</span>
                <span className="label">Multistructural</span>
              </div>
              <div className="summary-item">
                <span className="count">{soloDistribution.relational}</span>
                <span className="label">Relational</span>
              </div>
              <div className="summary-item">
                <span className="count">{soloDistribution.extended_abstract}</span>
                <span className="label">Extended Abstract</span>
              </div>
            </div>
          </div>
        )}

        {/* Create Button */}
        <div className="builder-actions">
          <button
            className="btn-primary btn-large"
            onClick={handleCreateQuiz}
            disabled={creating || !quizTitle.trim() || selectedQuestionIds.length === 0}
          >
            {creating ? 'Creating...' : `📝 Create Quiz (${selectedQuestionIds.length} questions)`}
          </button>
        </div>

        {/* Created Quiz */}
        {createdQuiz && (
          <div className="created-quiz">
            <h4>✅ Quiz Created!</h4>
            <p><strong>{createdQuiz.title}</strong></p>
            <p>{createdQuiz.question_count} questions</p>
            <button 
              className="btn-secondary"
              onClick={() => handleExportQuiz(createdQuiz.id)}
            >
              📥 Export to JSON
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default QuizBuilder;
