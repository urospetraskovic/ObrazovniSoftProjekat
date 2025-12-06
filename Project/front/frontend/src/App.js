import React, { useState } from 'react';
import axios from 'axios';
import './App.css';
import FileUpload from './components/FileUpload';
import QuizLoader from './components/QuizLoader';
import QuizDisplay from './components/QuizDisplay';

function App() {
  const [file, setFile] = useState(null);
  const [quizData, setQuizData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const API_URL = 'http://localhost:5000/api';

  const handleFileSelect = (selectedFile) => {
    setFile(selectedFile);
    setError(null);
    setSuccess(null);
  };

  const handleGenerateQuiz = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await axios.post(`${API_URL}/generate-quiz`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setQuizData(response.data);
      setSuccess('Quiz generated successfully!');
      setFile(null);
    } catch (err) {
      const errorMessage = err.response?.data?.error || err.message || 'Failed to generate quiz';
      setError(errorMessage);
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleClearQuiz = () => {
    setQuizData(null);
    setFile(null);
    setError(null);
    setSuccess(null);
  };

  const handleLoadQuiz = (loadedQuizData) => {
    setQuizData(loadedQuizData);
    setSuccess('Quiz loaded successfully!');
    setFile(null);
    setError(null);
  };

  const handleDownloadQuiz = async () => {
    if (!quizData) return;

    try {
      setLoading(true);
      // Send quiz to backend to save
      const response = await axios.post(`${API_URL}/save-quiz`, quizData);
      
      if (response.data.success) {
        setSuccess(`Quiz saved! File: ${response.data.filename}`);
      }
    } catch (err) {
      const errorMessage = err.response?.data?.error || err.message || 'Failed to save quiz';
      setError(errorMessage);
      console.error('Error saving quiz:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <div className="container">
        <div className="header">
          <h1>🎓 SOLO Taxonomy Quiz Generator</h1>
          <p>Upload educational content and generate adaptive quizzes using SOLO taxonomy</p>
        </div>

        {error && <div className="error">{error}</div>}
        {success && <div className="success">{success}</div>}

        {!quizData ? (
          <div className="main-content">
            <FileUpload
              file={file}
              onFileSelect={handleFileSelect}
              onGenerate={handleGenerateQuiz}
              loading={loading}
            />
            
            <QuizLoader
              onQuizLoad={handleLoadQuiz}
              loading={loading}
            />
            
            <div className="card">
              <h2>ℹ️ How it works</h2>
              <ul style={{ lineHeight: '1.8', color: '#555' }}>
                <li>📄 Upload a text file with educational content</li>
                <li>🧠 AI analyzes content and extracts key concepts</li>
                <li>📝 Generates questions across SOLO levels:</li>

                <li>✅ Preview quiz before downloading</li>
                <li>💾 Export as JSON for use anywhere</li>
              </ul>
            </div>
          </div>
        ) : (
          <QuizDisplay
            quizData={quizData}
            onDownload={handleDownloadQuiz}
            onClear={handleClearQuiz}
          />
        )}
      </div>
    </div>
  );
}

export default App;
