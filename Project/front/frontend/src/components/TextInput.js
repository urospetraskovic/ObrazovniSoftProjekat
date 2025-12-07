import React, { useState } from 'react';

function TextInput({ onTextSubmit, loading }) {
  const [textContent, setTextContent] = useState('');

  const handleSubmit = () => {
    if (textContent.trim()) {
      onTextSubmit(textContent);
      setTextContent('');
    } else {
      alert('Please enter some text');
    }
  };

  const handleClear = () => {
    setTextContent('');
  };

  const characterCount = textContent.length;
  const wordCount = textContent.trim().split(/\s+/).filter(w => w.length > 0).length;

  return (
    <div className="card">
      <h2>✍️ Direct Text Input</h2>
      <div className="text-input-section">
        <textarea
          className="text-area"
          value={textContent}
          onChange={(e) => setTextContent(e.target.value)}
          placeholder="Paste or type your content here to generate a quiz..."
          disabled={loading}
        />

        <div className="text-stats">
          <span>{characterCount} characters</span>
          <span>•</span>
          <span>{wordCount} words</span>
        </div>

        <div className="button-group">
          {textContent && (
            <button
              className="btn-secondary"
              onClick={handleClear}
              disabled={loading}
            >
              Clear
            </button>
          )}
          <button
            className="btn-primary"
            onClick={handleSubmit}
            disabled={!textContent.trim() || loading}
          >
            {loading ? (
              <span className="loading">
                <span className="spinner"></span>
                Generating...
              </span>
            ) : (
              '🚀 Generate Quiz'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export default TextInput;
