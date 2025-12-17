import React, { useState } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:5000/api';

function QuestionBank({ questions, courseId, onRefresh, onSuccess, onError }) {
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedQuestions, setSelectedQuestions] = useState([]);
  const [expandedQuestion, setExpandedQuestion] = useState(null);

  const filteredQuestions = questions.filter(q => {
    const matchesFilter = filter === 'all' || q.solo_level === filter;
    const matchesSearch = !searchTerm || 
      q.question_text?.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const handleSelectQuestion = (questionId) => {
    setSelectedQuestions(prev => 
      prev.includes(questionId) 
        ? prev.filter(id => id !== questionId)
        : [...prev, questionId]
    );
  };

  const handleSelectAll = () => {
    if (selectedQuestions.length === filteredQuestions.length) {
      setSelectedQuestions([]);
    } else {
      setSelectedQuestions(filteredQuestions.map(q => q.id));
    }
  };

  const handleDeleteQuestion = async (questionId) => {
    if (!window.confirm('Delete this question?')) return;

    try {
      await axios.delete(`${API_URL}/questions/${questionId}`);
      onSuccess('Question deleted');
      onRefresh();
    } catch (err) {
      onError('Failed to delete question');
    }
  };

  const getSoloLevelColor = (level) => {
    const colors = {
      unistructural: '#4CAF50',
      multistructural: '#2196F3',
      relational: '#FF9800',
      extended_abstract: '#9C27B0'
    };
    return colors[level] || '#gray';
  };

  const getSoloLevelIcon = (level) => {
    const icons = {
      unistructural: '①',
      multistructural: '②',
      relational: '③',
      extended_abstract: '④'
    };
    return icons[level] || '?';
  };

  const questionsByLevel = {
    all: questions.length,
    unistructural: questions.filter(q => q.solo_level === 'unistructural').length,
    multistructural: questions.filter(q => q.solo_level === 'multistructural').length,
    relational: questions.filter(q => q.solo_level === 'relational').length,
    extended_abstract: questions.filter(q => q.solo_level === 'extended_abstract').length
  };

  return (
    <div className="question-bank">
      <div className="card">
        <div className="card-header">
          <h2>❓ Question Bank</h2>
          <button className="btn-secondary" onClick={onRefresh}>
            🔄 Refresh
          </button>
        </div>

        {/* Filters */}
        <div className="filters-section">
          <div className="filter-tabs">
            {[
              { key: 'all', label: 'All' },
              { key: 'unistructural', label: 'Unistructural' },
              { key: 'multistructural', label: 'Multistructural' },
              { key: 'relational', label: 'Relational' },
              { key: 'extended_abstract', label: 'Extended Abstract' }
            ].map(({ key, label }) => (
              <button
                key={key}
                className={`filter-tab ${filter === key ? 'active' : ''}`}
                onClick={() => setFilter(key)}
                style={filter === key ? { borderColor: getSoloLevelColor(key) } : {}}
              >
                {label} ({questionsByLevel[key]})
              </button>
            ))}
          </div>
          
          <div className="search-box">
            <input
              type="text"
              placeholder="Search questions..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>

        {/* Selection Actions */}
        {selectedQuestions.length > 0 && (
          <div className="selection-actions">
            <span>{selectedQuestions.length} selected</span>
            <button 
              className="btn-secondary"
              onClick={() => setSelectedQuestions([])}
            >
              Clear Selection
            </button>
          </div>
        )}

        {/* Questions List */}
        {questions.length === 0 ? (
          <div className="empty-state">
            <p>No questions in the bank yet.</p>
            <p className="hint">Generate questions from your lessons first.</p>
          </div>
        ) : filteredQuestions.length === 0 ? (
          <div className="empty-state">
            <p>No questions match your filters.</p>
          </div>
        ) : (
          <div className="questions-list">
            <div className="list-header">
              <label className="select-all">
                <input
                  type="checkbox"
                  checked={selectedQuestions.length === filteredQuestions.length && filteredQuestions.length > 0}
                  onChange={handleSelectAll}
                />
                Select All
              </label>
            </div>

            {filteredQuestions.map((question) => (
              <div 
                key={question.id} 
                className={`question-card ${selectedQuestions.includes(question.id) ? 'selected' : ''}`}
              >
                <div className="question-select">
                  <input
                    type="checkbox"
                    checked={selectedQuestions.includes(question.id)}
                    onChange={() => handleSelectQuestion(question.id)}
                  />
                </div>
                
                <div 
                  className="question-content"
                  onClick={() => setExpandedQuestion(
                    expandedQuestion === question.id ? null : question.id
                  )}
                >
                  <div className="question-header">
                    <span 
                      className="solo-badge"
                      style={{ backgroundColor: getSoloLevelColor(question.solo_level) }}
                    >
                      {getSoloLevelIcon(question.solo_level)} {question.solo_level?.replace('_', ' ')}
                    </span>
                    <span className="question-type">{question.question_type}</span>
                  </div>
                  
                  <p className="question-text">{question.question_text}</p>
                  
                  {/* Lesson Source */}
                  <div className="lesson-source">
                    <span className="source-icon">📚</span>
                    {question.secondary_lesson_title ? (
                      <span className="source-text">
                        From <strong>{question.primary_lesson_title}</strong> + <strong>{question.secondary_lesson_title}</strong>
                      </span>
                    ) : question.primary_lesson_title ? (
                      <span className="source-text">
                        From <strong>{question.primary_lesson_title}</strong>
                      </span>
                    ) : null}
                  </div>

                  {expandedQuestion === question.id && (
                    <div className="question-details">
                      {question.options && (
                        <div className="options-list">
                          {question.options.map((opt, i) => (
                            <div 
                              key={i} 
                              className={`option ${i === question.correct_option_index ? 'correct' : ''}`}
                            >
                              {opt}
                              {i === question.correct_option_index && <span className="correct-mark">✓</span>}
                            </div>
                          ))}
                        </div>
                      )}
                      
                      {question.explanation && (
                        <div className="explanation">
                          <strong>Explanation:</strong> {question.explanation}
                        </div>
                      )}

                      {question.tags && question.tags.length > 0 && (
                        <div className="tags">
                          {question.tags.map((tag, i) => (
                            <span key={i} className="tag">{tag}</span>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                <div className="question-actions">
                  <button
                    className="btn-icon btn-danger"
                    onClick={() => handleDeleteQuestion(question.id)}
                    title="Delete question"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Stats */}
        <div className="bank-stats">
          <div className="stat">
            <span className="stat-value">{questions.length}</span>
            <span className="stat-label">Total Questions</span>
          </div>
          <div className="stat">
            <span className="stat-value">{questionsByLevel.unistructural}</span>
            <span className="stat-label">Unistructural</span>
          </div>
          <div className="stat">
            <span className="stat-value">{questionsByLevel.multistructural}</span>
            <span className="stat-label">Multistructural</span>
          </div>
          <div className="stat">
            <span className="stat-value">{questionsByLevel.relational}</span>
            <span className="stat-label">Relational</span>
          </div>
          <div className="stat">
            <span className="stat-value">{questionsByLevel.extended_abstract}</span>
            <span className="stat-label">Extended Abstract</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default QuestionBank;
