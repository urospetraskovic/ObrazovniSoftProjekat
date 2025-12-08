import React, { useState } from 'react';

function QuizDisplay({ quizData, onDownload, onClear }) {
  const [expandedQuestions, setExpandedQuestions] = useState({});
  const [editingChapter, setEditingChapter] = useState(null);
  const [chapterTitles, setChapterTitles] = useState(
    (quizData.chapters || []).reduce((acc, ch) => {
      acc[`ch-${ch.chapter_number}`] = ch.title || `Chapter ${ch.chapter_number}`;
      return acc;
    }, {})
  );
  const [removedQuestions, setRemovedQuestions] = useState(new Set());

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

  const handleRemoveQuestion = (chapterIdx, qIdx) => {
    const key = `q-${chapterIdx}-${qIdx}`;
    setRemovedQuestions((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(key)) {
        newSet.delete(key);
      } else {
        newSet.add(key);
      }
      return newSet;
    });
  };

  const handleChapterTitleChange = (chapterNum, newTitle) => {
    setChapterTitles((prev) => ({
      ...prev,
      [`ch-${chapterNum}`]: newTitle,
    }));
  };

  const handleResetChapterTitle = (chapterNum) => {
    setChapterTitles((prev) => ({
      ...prev,
      [`ch-${chapterNum}`]: `Chapter ${chapterNum}`,
    }));
  };

  const handleDownloadWithChanges = async () => {
    // Create modified quiz data
    const modifiedQuizData = {
      ...quizData,
      chapters: quizData.chapters.map((chapter, chIdx) => ({
        ...chapter,
        title: chapterTitles[`ch-${chapter.chapter_number}`] || chapter.title,
        questions: chapter.questions.filter((_, qIdx) => {
          return !removedQuestions.has(`q-${chIdx}-${qIdx}`);
        }),
      })),
    };

    // Pass modified data to the parent handler
    onDownload(modifiedQuizData);
  };

  const chapters = quizData.chapters || [];
  const totalQuestions = chapters.reduce((sum, chapter) => {
    const visibleQuestions = (chapter.questions || []).filter((_, qIdx) => {
      return !removedQuestions.has(`q-${chapters.indexOf(chapter)}-${qIdx}`);
    });
    return sum + visibleQuestions.length;
  }, 0);

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
            {editingChapter === chapterIdx ? (
              <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                <input
                  type="text"
                  value={chapterTitles[`ch-${chapter.chapter_number}`]}
                  onChange={(e) => handleChapterTitleChange(chapter.chapter_number, e.target.value)}
                  style={{
                    flex: 1,
                    padding: '8px 12px',
                    fontSize: '16px',
                    border: '2px solid #007bff',
                    borderRadius: '4px',
                    fontWeight: 'bold',
                  }}
                  autoFocus
                />
                <button
                  onClick={() => setEditingChapter(null)}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: '#28a745',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '14px',
                  }}
                >
                  ✓
                </button>
                <button
                  onClick={() => {
                    handleResetChapterTitle(chapter.chapter_number);
                    setEditingChapter(null);
                  }}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: '#dc3545',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '14px',
                  }}
                >
                  Reset
                </button>
              </div>
            ) : (
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>Chapter {chapter.chapter_number}: {chapterTitles[`ch-${chapter.chapter_number}`] || 'Untitled'}</span>
                <button
                  onClick={() => setEditingChapter(chapterIdx)}
                  style={{
                    padding: '6px 12px',
                    backgroundColor: '#007bff',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '12px',
                  }}
                >
                  ✏️ Edit Title
                </button>
              </div>
            )}
          </div>

          {chapter.questions?.map((questionSet, qIdx) => {
            const qId = `q-${chapterIdx}-${qIdx}`;
            const isExpanded = expandedQuestions[qId];
            const isRemoved = removedQuestions.has(qId);

            return (
              <div key={qIdx} className="question-card" style={{
                opacity: isRemoved ? 0.5 : 1,
                backgroundColor: isRemoved ? '#f8d7da' : 'white',
                borderLeft: isRemoved ? '4px solid #dc3545' : '4px solid #007bff',
              }}>
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
                    {isRemoved && (
                      <div style={{
                        color: '#dc3545',
                        fontSize: '12px',
                        fontWeight: 'bold',
                        marginTop: '5px',
                      }}>
                        ❌ This question will be removed
                      </div>
                    )}
                  </div>
                  <div style={{ display: 'flex', gap: '10px', marginLeft: '10px' }}>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRemoveQuestion(chapterIdx, qIdx);
                      }}
                      style={{
                        padding: '6px 12px',
                        backgroundColor: isRemoved ? '#28a745' : '#dc3545',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '12px',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {isRemoved ? '↩️ Keep' : '🗑️ Remove'}
                    </button>
                    <span style={{ fontSize: '1.5em' }}>
                      {isExpanded ? '▼' : '▶'}
                    </span>
                  </div>
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
        <div style={{ marginBottom: '10px', color: '#666', fontSize: '14px' }}>
          {removedQuestions.size > 0 && (
            <p>🗑️ {removedQuestions.size} question(s) marked for removal</p>
          )}
        </div>
        <button className="btn-primary btn-download" onClick={handleDownloadWithChanges}>
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
