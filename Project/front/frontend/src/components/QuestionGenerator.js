import React, { useState, useEffect } from 'react';
import { questionApi } from '../api';

function QuestionGenerator({ course, onQuestionsGenerated, onSuccess, onError }) {
  const [lessons, setLessons] = useState([]);
  const [selectedLessons, setSelectedLessons] = useState([]);
  const [soloLevels, setSoloLevels] = useState({
    unistructural: true,
    multistructural: true,
    relational: true,
    extended_abstract: false
  });
  const [questionsPerLevel, setQuestionsPerLevel] = useState(3);
  const [generating, setGenerating] = useState(false);
  const [progress, setProgress] = useState(null);

  useEffect(() => {
    if (course?.lessons) {
      // Filter to only show parsed lessons
      const parsedLessons = course.lessons.filter(l => l.section_count > 0);
      setLessons(parsedLessons);
    }
  }, [course]);

  const handleLessonToggle = (lessonId) => {
    setSelectedLessons(prev => {
      if (prev.includes(lessonId)) {
        return prev.filter(id => id !== lessonId);
      } else {
        // For extended abstract, allow max 2 lessons
        if (prev.length >= 2 && soloLevels.extended_abstract) {
          onError('For Extended Abstract questions, select exactly 2 lessons');
          return prev;
        }
        return [...prev, lessonId];
      }
    });
  };

  const handleSoloLevelToggle = (level) => {
    setSoloLevels(prev => {
      const newState = { ...prev, [level]: !prev[level] };
      
      // If enabling extended_abstract, ensure 2 lessons are selected
      if (level === 'extended_abstract' && !prev[level]) {
        if (selectedLessons.length < 2) {
          onError('Extended Abstract requires 2 lessons. Please select another lesson.');
        }
      }
      
      return newState;
    });
  };

  const handleGenerate = async () => {
    if (selectedLessons.length === 0) {
      onError('Please select at least one lesson');
      return;
    }

    const activeLevels = Object.entries(soloLevels)
      .filter(([_, active]) => active)
      .map(([level]) => level);

    if (activeLevels.length === 0) {
      onError('Please select at least one SOLO level');
      return;
    }

    if (soloLevels.extended_abstract && selectedLessons.length < 2) {
      onError('Extended Abstract questions require 2 lessons selected');
      return;
    }

    try {
      setGenerating(true);
      setProgress('Generating questions...');

      const response = await questionApi.generate({
        lesson_ids: selectedLessons,
        solo_levels: activeLevels,
        questions_per_level: questionsPerLevel,
        save_to_db: true
      });

      const { questions, count, solo_distribution } = response.data;
      
      setProgress(null);
      onQuestionsGenerated(questions);
      
      // Show distribution summary
      const summary = Object.entries(solo_distribution)
        .filter(([_, count]) => count > 0)
        .map(([level, count]) => `${level}: ${count}`)
        .join(', ');
      onSuccess(`Generated ${count} questions! (${summary})`);

    } catch (err) {
      onError(err.response?.data?.error || 'Failed to generate questions');
    } finally {
      setGenerating(false);
      setProgress(null);
    }
  };

  const getSoloLevelDescription = (level) => {
    const descriptions = {
      unistructural: 'From Learning Objects - identify, name, define single facts',
      multistructural: 'From Sections - list, describe, enumerate multiple facts',
      relational: 'From Sections + Learning Objects - compare, explain, relate',
      extended_abstract: 'From 2 Lessons combined - generalize, create, hypothesize'
    };
    return descriptions[level] || '';
  };

  const unparsedLessons = (course?.lessons || []).filter(l => !l.section_count || l.section_count === 0);

  return (
    <div className="question-generator">
      <div className="card">
        <h2>Generate Questions</h2>
        <p className="subtitle">Select lessons and SOLO levels to generate questions</p>

        {/* Lesson Selection */}
        <div className="generator-section">
          <h3>Select Lessons</h3>
          {lessons.length === 0 ? (
            <div className="empty-state">
              <p>No parsed lessons available.</p>
              <p className="hint">Go to Lessons tab and parse your PDF files first.</p>
            </div>
          ) : (
            <div className="lesson-select-grid">
              {lessons.map((lesson) => (
                <div
                  key={lesson.id}
                  className={`lesson-select-card ${selectedLessons.includes(lesson.id) ? 'selected' : ''}`}
                  onClick={() => handleLessonToggle(lesson.id)}
                >
                  <div className="checkbox">
                    {selectedLessons.includes(lesson.id) ? '✓' : ''}
                  </div>
                  <div className="lesson-select-info">
                    <h4>{lesson.title}</h4>
                    <span>{lesson.section_count} sections</span>
                  </div>
                </div>
              ))}
            </div>
          )}
          
          {selectedLessons.length > 0 && (
            <p className="selection-info">
              {selectedLessons.length} lesson(s) selected
              {soloLevels.extended_abstract && selectedLessons.length === 2 && (
                <span className="good"> - Ready for Extended Abstract</span>
              )}
            </p>
          )}

          {unparsedLessons.length > 0 && (
            <p className="warning-hint">
              {unparsedLessons.length} lesson(s) need parsing before they can be used
            </p>
          )}
        </div>

        {/* SOLO Level Selection */}
        <div className="generator-section">
          <h3>SOLO Levels</h3>
          <div className="solo-level-grid">
            {Object.entries(soloLevels).map(([level, active]) => (
              <div
                key={level}
                className={`solo-level-card ${active ? 'active' : ''} ${level === 'extended_abstract' && selectedLessons.length < 2 ? 'disabled' : ''}`}
                onClick={() => handleSoloLevelToggle(level)}
              >
                <div className="solo-header">
                  <div className="checkbox">{active ? '✓' : ''}</div>
                  <h4>{level.replace('_', ' ')}</h4>
                </div>
                <p className="solo-desc">{getSoloLevelDescription(level)}</p>
                {level === 'extended_abstract' && (
                  <span className="solo-note">Requires 2 lessons</span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Questions Per Level */}
        <div className="generator-section">
          <h3>Questions per Level</h3>
          <div className="questions-slider">
            <input
              type="range"
              min="1"
              max="10"
              value={questionsPerLevel}
              onChange={(e) => setQuestionsPerLevel(parseInt(e.target.value))}
            />
            <span className="slider-value">{questionsPerLevel}</span>
          </div>
          <p className="estimate">
            Estimated total: ~{Object.values(soloLevels).filter(Boolean).length * questionsPerLevel} questions
          </p>
        </div>

        {/* Generate Button */}
        <div className="generator-actions">
          {progress && (
            <div className="progress-message">
              <span className="spinner"></span> {progress}
            </div>
          )}
          <button
            className="btn-primary btn-large"
            onClick={handleGenerate}
            disabled={generating || selectedLessons.length === 0}
          >
            {generating ? 'Generating...' : 'Generate Questions'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default QuestionGenerator;
