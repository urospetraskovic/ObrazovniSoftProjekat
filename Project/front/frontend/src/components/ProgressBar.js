import React from 'react';

function ProgressBar({ progress, message }) {
  if (!progress) return null;

  const percentage = progress.total_questions_target 
    ? Math.round((progress.questions_generated / progress.total_questions_target) * 100)
    : 0;

  return (
    <div className="progress-container">
      <div className="progress-info">
        <p className="progress-message">{message || 'Generating quiz...'}</p>
        <div className="progress-stats">
          <span className="stat">Chapter {progress.chapters_completed} of {progress.total_chapters}</span>
          <span className="stat">Question {progress.questions_generated} of {progress.total_questions_target}</span>
        </div>
      </div>
      <div className="progress-bar-wrapper">
        <div className="progress-bar">
          <div 
            className="progress-fill" 
            style={{ width: `${percentage}%` }}
          >
            <span className="progress-text">{percentage}%</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ProgressBar;
