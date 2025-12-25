import React, { useState, useRef } from 'react';
import { lessonApi } from '../api';

function LessonManager({ course, onSelectLesson, onLessonsChange, onSuccess, onError, onBack, loading }) {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      onError('Only PDF files are allowed');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', file.name.replace('.pdf', '').replace(/_/g, ' '));

    try {
      setUploading(true);
      setUploadProgress('Uploading PDF...');
      
      await lessonApi.create(course.id, formData);

      onSuccess('Lesson uploaded! Click "Parse" to extract sections.');
      onLessonsChange();
      fileInputRef.current.value = '';
    } catch (err) {
      onError(err.response?.data?.error || 'Failed to upload lesson');
    } finally {
      setUploading(false);
      setUploadProgress(null);
    }
  };

  const handleParseLesson = async (lessonId, e) => {
    e.stopPropagation();
    
    try {
      setUploadProgress(`Parsing lesson... This may take a minute.`);
      const response = await lessonApi.parse(lessonId);
      
      const { section_count, learning_object_count } = response.data;
      onSuccess(`Parsed ${section_count} sections with ${learning_object_count} learning objects!`);
      onLessonsChange();
    } catch (err) {
      onError(err.response?.data?.error || 'Failed to parse lesson');
    } finally {
      setUploadProgress(null);
    }
  };

  const handleDeleteLesson = async (lessonId, e) => {
    e.stopPropagation();
    if (!window.confirm('Delete this lesson and all its content?')) return;

    try {
      await lessonApi.delete(lessonId);
      onSuccess('Lesson deleted');
      onLessonsChange();
    } catch (err) {
      onError('Failed to delete lesson');
    }
  };

  const lessons = course.lessons || [];

  return (
    <div className="lesson-manager">
      <div className="card">
        <div className="card-header">
          <div>
            <button className="btn-back" onClick={onBack}>← Back to Courses</button>
            <h2>📖 Lessons in {course.name}</h2>
          </div>
          <div className="upload-button-wrapper">
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              onChange={handleFileUpload}
              style={{ display: 'none' }}
              id="lesson-upload"
            />
            <label htmlFor="lesson-upload" className="btn-primary">
              {uploading ? 'Uploading...' : '📄 Upload PDF Lesson'}
            </label>
          </div>
        </div>

        {uploadProgress && (
          <div className="progress-message">
            <span className="spinner"></span> {uploadProgress}
          </div>
        )}

        {loading ? (
          <div className="loading-state">Loading lessons...</div>
        ) : lessons.length === 0 ? (
          <div className="empty-state">
            <p>No lessons yet. Upload your first PDF lesson!</p>
            <p className="hint">Lessons are PDF files containing educational content (e.g., "Virtual Memory.pdf")</p>
          </div>
        ) : (
          <div className="lesson-list">
            {lessons.map((lesson) => (
              <div 
                key={lesson.id} 
                className="lesson-card"
                onClick={() => onSelectLesson(lesson)}
              >
                <div className="lesson-info">
                  <h3>📄 {lesson.title}</h3>
                  {lesson.filename && (
                    <p className="filename">{lesson.filename}</p>
                  )}
                  <div className="lesson-stats">
                    <span>📑 {lesson.section_count || 0} Sections</span>
                    {lesson.summary && <span className="parsed-badge">✓ Parsed</span>}
                  </div>
                </div>
                <div className="lesson-actions">
                  {!lesson.section_count || lesson.section_count === 0 ? (
                    <button 
                      className="btn-secondary"
                      onClick={(e) => handleParseLesson(lesson.id, e)}
                      title="Parse lesson to extract sections"
                    >
                      🔍 Parse
                    </button>
                  ) : (
                    <button 
                      className="btn-secondary"
                      onClick={(e) => { e.stopPropagation(); onSelectLesson(lesson); }}
                    >
                      View Content
                    </button>
                  )}
                  <button 
                    className="btn-icon btn-danger"
                    onClick={(e) => handleDeleteLesson(lesson.id, e)}
                    title="Delete lesson"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="help-section">
          <h4>📋 Lesson Workflow</h4>
          <ol>
            <li><strong>Upload:</strong> Add a PDF lesson file</li>
            <li><strong>Parse:</strong> AI extracts sections and learning objects</li>
            <li><strong>Review:</strong> View the extracted content structure</li>
            <li><strong>Generate:</strong> Create questions from parsed content</li>
          </ol>
        </div>
      </div>
    </div>
  );
}

export default LessonManager;
