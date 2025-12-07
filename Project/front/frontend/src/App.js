import React, { useState } from 'react';
import axios from 'axios';
import './App.css';
import FileUpload from './components/FileUpload';
import QuizLoader from './components/QuizLoader';
import QuizDisplay from './components/QuizDisplay';
import TextInput from './components/TextInput';
import QuizConfig from './components/QuizConfig';

function App() {
  const [file, setFile] = useState(null);
  const [quizData, setQuizData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [showConfig, setShowConfig] = useState(false);
  const [pendingConfig, setPendingConfig] = useState(null);

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

    // Show config dialog instead of generating directly
    setPendingConfig({ type: 'file', file: file });
    setShowConfig(true);
  };

  const handleGenerateWithConfig = async (config) => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('config', JSON.stringify(config));

    setLoading(true);
    setError(null);
    setSuccess(null);
    setShowConfig(false);

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
      setPendingConfig(null);
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

  const handleTextInput = async (textContent) => {
    // Show config dialog for text input
    setPendingConfig({ type: 'text', content: textContent });
    setShowConfig(true);
  };

  const handleGenerateFromTextWithConfig = async (config) => {
    if (!pendingConfig || pendingConfig.type !== 'text') {
      setError('Invalid state for text generation');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);
    setShowConfig(false);

    try {
      const response = await axios.post(`${API_URL}/generate-quiz-from-text`, {
        content: pendingConfig.content,
        config: config,
      });

      setQuizData(response.data);
      setSuccess('Quiz generated successfully from text!');
      setFile(null);
    } catch (err) {
      const errorMessage = err.response?.data?.error || err.message || 'Failed to generate quiz';
      setError(errorMessage);
      console.error('Error:', err);
    } finally {
      setLoading(false);
      setPendingConfig(null);
    }
  };

  const handleConfigApply = (config) => {
    if (pendingConfig?.type === 'file') {
      handleGenerateWithConfig(config);
    } else if (pendingConfig?.type === 'text') {
      handleGenerateFromTextWithConfig(config);
    }
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
      {showConfig && (
        <QuizConfig
          onApply={handleConfigApply}
          onCancel={() => {
            setShowConfig(false);
            setPendingConfig(null);
          }}
          loading={loading}
        />
      )}

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
            
            <TextInput
              onTextSubmit={handleTextInput}
              loading={loading}
            />
            
            <QuizLoader
              onQuizLoad={handleLoadQuiz}
              loading={loading}
            />
            
            <div className="card">
              <h2>ℹ️ How it works</h2>
              <ul style={{ lineHeight: '1.8', color: '#555' }}>
                <li>📄 Upload a text file or PDF with educational content</li>
                <li>✍️ Or paste text directly for quick quiz generation</li>
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
