import React from 'react';

function TopBar({ selectedCourse, selectedLesson, apiStatus }) {
  return (
    <div className="top-bar">
      <div className="breadcrumb-container">
        {selectedCourse ? (
          <>
            <strong>{selectedCourse.name}</strong>
            {selectedLesson && (
              <>
                <span className="breadcrumb-separator">/</span>
                <strong>{selectedLesson.title}</strong>
              </>
            )}
          </>
        ) : (
          <strong>Welcome to SOLO Quiz Generator</strong>
        )}
      </div>
      <div className="top-bar-actions">
        {apiStatus?.api_exhausted && (
          <div className="api-warning">API Keys Exhausted</div>
        )}
      </div>
    </div>
  );
}

export default TopBar;
