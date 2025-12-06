import React, { useRef } from 'react';

function QuizLoader({ onQuizLoad, loading }) {
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.type === 'application/json') {
      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const quizData = JSON.parse(event.target.result);
          onQuizLoad(quizData);
        } catch (error) {
          alert('Invalid JSON file. Please select a valid quiz file.');
        }
      };
      reader.readAsText(selectedFile);
    } else {
      alert('Please select a .json quiz file');
    }
  };

  return (
    <div className="card">
      <h2>📂 Load Previous Quiz</h2>
      <div className="upload-section">
        <div className="file-input-wrapper">
          <input
            ref={fileInputRef}
            type="file"
            accept=".json"
            onChange={handleFileChange}
            id="quiz-file-input"
          />
          <label
            htmlFor="quiz-file-input"
            className="file-input-label"
          >
            📋 Click to load a .json quiz file
          </label>
        </div>

        <div className="button-group">
          <button
            className="btn-primary"
            onClick={() => fileInputRef.current?.click()}
            disabled={loading}
          >
            {loading ? 'Loading...' : 'Browse Files'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default QuizLoader;
