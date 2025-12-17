import React, { useState } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:5000/api';

function CourseManager({ courses, onSelectCourse, onCoursesChange, onSuccess, onError, loading }) {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newCourse, setNewCourse] = useState({ name: '', code: '', description: '' });
  const [creating, setCreating] = useState(false);

  const handleCreateCourse = async (e) => {
    e.preventDefault();
    if (!newCourse.name.trim()) {
      onError('Course name is required');
      return;
    }

    try {
      setCreating(true);
      await axios.post(`${API_URL}/courses`, newCourse);
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
      await axios.delete(`${API_URL}/courses/${courseId}`);
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
          <h2>📚 Your Courses</h2>
          <button 
            className="btn-primary"
            onClick={() => setShowCreateForm(!showCreateForm)}
          >
            {showCreateForm ? '✕ Cancel' : '+ New Course'}
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
                    <span>📖 {course.lesson_count || 0} Lessons</span>
                  </div>
                </div>
                <div className="course-actions">
                  <button 
                    className="btn-icon"
                    onClick={(e) => handleDeleteCourse(course.id, e)}
                    title="Delete course"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default CourseManager;
