import React, { useState } from 'react';

function QuizDisplay({ quizData, onDownload, onClear }) {
  const [expandedQuestions, setExpandedQuestions] = useState({});

  const toggleQuestion = (id) => {
    setExpandedQuestions((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const getLevelColor = (level) => {
    const levelMap = {
      prestructural: 'prestructural',
      unistructural: 'unistructural',
      multistructural: 'multistructural',
      relational: 'relational',
      extended_abstract: 'extended-abstract',
    };
    return levelMap[level] || 'prestructural';
  };

  const getLevelLabel = (level) => {
    const labelMap = {
      prestructural: '1️⃣ Prestructural',
      unistructural: '2️⃣ Unistructural',
      multistructural: '3️⃣ Multistructural',
      relational: '4️⃣ Relational',
      extended_abstract: '5️⃣ Extended Abstract',
    };
    return labelMap[level] || level;
  };

  const chapters = quizData.chapters || [];
  const totalQuestions = chapters.reduce((sum, chapter) => sum + (chapter.questions?.length || 0), 0);

  return (
    <div className="quiz-container">
      <div className="quiz-header">
        <h2>📋 Generated Quiz</h2>
        <p style={{ color: '#666', marginTop: '5px' }}>
          {chapters.length} chapter{chapters.length !== 1 ? 's' : ''} • {totalQuestions} questions
        </p>
        <div className="quiz-progress">
          <div className="quiz-progress-bar" style={{ width: '100%' }}></div>
        </div>
      </div>

      {chapters.map((chapter, chapterIdx) => (
        <div key={chapterIdx} className="chapter-section">
          <div className="chapter-title">
            Chapter {chapter.chapter_number}: {chapter.title || 'Untitled'}
          </div>

          {chapter.questions?.map((questionSet, qIdx) => {
            const qId = `q-${chapterIdx}-${qIdx}`;
            const isExpanded = expandedQuestions[qId];

            return (
              <div key={qIdx} className="question-card">
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'start',
                    cursor: 'pointer',
                  }}
                  onClick={() => toggleQuestion(qId)}
                >
                  <div style={{ flex: 1 }}>
                    <div className={`question-level ${getLevelColor(questionSet.solo_level)}`}>
                      {getLevelLabel(questionSet.solo_level)}
                    </div>
                    <div className="question-text">
                      {questionSet.question_data?.question || 'No question text'}
                    </div>
                  </div>
                  <span style={{ fontSize: '1.5em', marginLeft: '10px' }}>
                    {isExpanded ? '▼' : '▶'}
                  </span>
                </div>

                {isExpanded && (
                  <div style={{ marginTop: '20px' }}>
                    <div className="options">
                      {questionSet.question_data?.options?.map((option, optIdx) => (
                        <div
                          key={optIdx}
                          className={`option ${
                            option.includes(questionSet.question_data?.correct_answer) ? 'correct' : ''
                          }`}
                        >
                          {option}
                        </div>
                      ))}
                    </div>

                    <div className="explanation">
                      <strong>Explanation:</strong> {questionSet.question_data?.explanation || 'No explanation provided'}
                    </div>

                    <div className="stats">
                      <strong>Correct Answer:</strong> {questionSet.question_data?.correct_answer}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ))}

      <div className="download-section">
        <button className="btn-primary btn-download" onClick={onDownload}>
          💾 Download Quiz (JSON)
        </button>
        <button
          className="btn-secondary"
          onClick={onClear}
          style={{ marginLeft: '10px' }}
        >
          ↺ Generate New Quiz
        </button>
      </div>
    </div>
  );
}

export default QuizDisplay;
