import React, { useState } from 'react';
import { courseApi } from '../api';
import { useLanguage } from '../context/LanguageContext';
import TranslationViewer from './TranslationViewer';

function CourseManager({ courses, onSelectCourse, onCoursesChange, onSuccess, onError, loading }) {
  const { selectedLanguage } = useLanguage();
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newCourse, setNewCourse] = useState({ name: '', code: '', description: '' });
  const [creating, setCreating] = useState(false);
  const [showTranslationViewer, setShowTranslationViewer] = useState(false);
  const [viewingTranslationId, setViewingTranslationId] = useState(null);

  const handleCreateCourse = async (e) => {
    e.preventDefault();
    if (!newCourse.name.trim()) {
      onError('Course name is required');
      return;
    }

    try {
      setCreating(true);
      await courseApi.create(newCourse);
      setNewCourse({ name: '', code: '', description: '' });
      setShowCreateForm(false);
      onSuccess('Course created successfully!');
      onCoursesChange();
    } catch (err) {
      onError(err.response?.data?.error || 'Failed to create course');
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteCourse = async (courseId, e) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure? This will delete all lessons and questions in this course.')) {
      return;
    }

    try {
      await courseApi.delete(courseId);
      onSuccess('Course deleted');
      onCoursesChange();
    } catch (err) {
      onError('Failed to delete course');
    }
  };

  return (
    <div className="course-manager">
      <div className="card">
        <div className="card-header">
          <h2>Your Courses</h2>
          <button 
            className="btn-primary"
            onClick={() => setShowCreateForm(!showCreateForm)}
          >
            {showCreateForm ? 'Cancel' : '+ New Course'}
          </button>
        </div>

        {showCreateForm && (
          <form className="create-form" onSubmit={handleCreateCourse}>
            <div className="form-group">
              <label>Course Name *</label>
              <input
                type="text"
                placeholder="e.g., Operating Systems"
                value={newCourse.name}
                onChange={(e) => setNewCourse({ ...newCourse, name: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label>Course Code</label>
              <input
                type="text"
                placeholder="e.g., CS301, OS"
                value={newCourse.code}
                onChange={(e) => setNewCourse({ ...newCourse, code: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Description</label>
              <textarea
                placeholder="Brief description of the course"
                value={newCourse.description}
                onChange={(e) => setNewCourse({ ...newCourse, description: e.target.value })}
                rows={3}
              />
            </div>
            <button type="submit" className="btn-primary" disabled={creating}>
              {creating ? 'Creating...' : 'Create Course'}
            </button>
          </form>
        )}

        {loading ? (
          <div className="loading-state">Loading courses...</div>
        ) : courses.length === 0 ? (
          <div className="empty-state">
            <p>No courses yet. Create your first course to get started!</p>
          </div>
        ) : (
          <div className="course-list">
            {courses.map((course) => (
              <div 
                key={course.id} 
                className="course-card"
                onClick={() => onSelectCourse(course)}
              >
                <div className="course-info">
                  <h3>
                    {course.code && <span className="course-code">{course.code}</span>}
                    {course.name}
                  </h3>
                  {course.description && <p>{course.description}</p>}
                  <div className="course-stats">
                    <span>{course.lesson_count || 0} Lessons</span>
                  </div>
                </div>
                <div className="course-actions">
                  <button 
                    className="btn-translate"
                    onClick={(e) => {
                      e.stopPropagation();
                      setViewingTranslationId(course.id);
                      setShowTranslationViewer(true);
                    }}
                    title={`View course in ${selectedLanguage}`}
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
                  </button>
                  <button 
                    className="btn-icon btn-danger"
                    onClick={(e) => handleDeleteCourse(course.id, e)}
                    title="Delete course"
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      
      <TranslationViewer
        isOpen={showTranslationViewer}
        onClose={() => {
          setShowTranslationViewer(false);
          setViewingTranslationId(null);
        }}
        entityId={viewingTranslationId}
        entityType="lesson"
        originalText={courses.find(c => c.id === viewingTranslationId)?.name}
      />
    </div>
  );
}

export default CourseManager;
