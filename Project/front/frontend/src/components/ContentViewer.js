import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:5000/api';

function ContentViewer({ lesson, onBack, onSuccess, onError, onLessonUpdate }) {
  const [sections, setSections] = useState([]);
  const [expandedSection, setExpandedSection] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (lesson?.sections) {
      setSections(lesson.sections);
    } else {
      fetchSections();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lesson]);

  const fetchSections = async () => {
    if (!lesson?.id) return;
    
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/lessons/${lesson.id}/sections`);
      setSections(response.data.sections || []);
    } catch (err) {
      onError('Failed to fetch sections');
    } finally {
      setLoading(false);
    }
  };

  const fetchLearningObjects = async (sectionId) => {
    try {
      const response = await axios.get(`${API_URL}/sections/${sectionId}`);
      const updatedSection = response.data.section;
      
      setSections(sections.map(s => 
        s.id === sectionId ? { ...s, learning_objects: updatedSection.learning_objects } : s
      ));
    } catch (err) {
      console.error('Failed to fetch learning objects:', err);
    }
  };

  const toggleSection = (sectionId) => {
    if (expandedSection === sectionId) {
      setExpandedSection(null);
    } else {
      setExpandedSection(sectionId);
      // Fetch learning objects if not already loaded
      const section = sections.find(s => s.id === sectionId);
      if (section && !section.learning_objects) {
        fetchLearningObjects(sectionId);
      }
    }
  };

  const handleParseLesson = async () => {
    try {
      setLoading(true);
      const response = await axios.post(`${API_URL}/lessons/${lesson.id}/parse`);
      
      const { sections: newSections, section_count, learning_object_count } = response.data;
      setSections(newSections || []);
      onSuccess(`Parsed ${section_count} sections with ${learning_object_count} learning objects!`);
      
      // Update parent with new lesson data
      if (onLessonUpdate) {
        onLessonUpdate({ ...lesson, sections: newSections, section_count });
      }
    } catch (err) {
      onError(err.response?.data?.error || 'Failed to parse lesson');
    } finally {
      setLoading(false);
    }
  };

  const getLearningObjectTypeIcon = (type) => {
    const icons = {
      concept: '💡',
      definition: '📖',
      procedure: '📋',
      principle: '⚖️',
      example: '📝',
      fact: '✓'
    };
    return icons[type] || '📌';
  };

  return (
    <div className="content-viewer">
      <div className="card">
        <div className="card-header">
          <div>
            <button className="btn-back" onClick={onBack}>← Back to Lessons</button>
            <h2>📄 {lesson.title}</h2>
            {lesson.filename && <span className="filename">{lesson.filename}</span>}
          </div>
          {sections.length === 0 && (
            <button 
              className="btn-primary" 
              onClick={handleParseLesson}
              disabled={loading}
            >
              {loading ? 'Parsing...' : '🔍 Parse Content'}
            </button>
          )}
        </div>

        {lesson.summary && (
          <div className="lesson-summary">
            <h4>📋 Summary</h4>
            <p>{lesson.summary}</p>
          </div>
        )}

        {loading ? (
          <div className="loading-state">
            <span className="spinner"></span> Parsing lesson content...
          </div>
        ) : sections.length === 0 ? (
          <div className="empty-state">
            <p>This lesson hasn't been parsed yet.</p>
            <p>Click "Parse Content" to extract sections and learning objects using AI.</p>
          </div>
        ) : (
          <div className="sections-list">
            <h3>📑 Sections ({sections.length})</h3>
            
            {sections.map((section, idx) => (
              <div key={section.id} className="section-card">
                <div 
                  className="section-header"
                  onClick={() => toggleSection(section.id)}
                >
                  <div className="section-title">
                    <span className="section-number">{idx + 1}</span>
                    <h4>{section.title}</h4>
                    {section.start_page && section.end_page && (
                      <span className="page-range">
                        Pages {section.start_page}-{section.end_page}
                      </span>
                    )}
                  </div>
                  <div className="section-meta">
                    <span className="lo-count">
                      {section.learning_object_count || 0} Learning Objects
                    </span>
                    <span className="expand-icon">
                      {expandedSection === section.id ? '▼' : '▶'}
                    </span>
                  </div>
                </div>

                {expandedSection === section.id && (
                  <div className="section-content">
                    {section.summary && (
                      <div className="section-summary">
                        <p>{section.summary}</p>
                      </div>
                    )}

                    {section.learning_objects && section.learning_objects.length > 0 ? (
                      <div className="learning-objects">
                        <h5>Learning Objects:</h5>
                        {section.learning_objects.map((lo) => (
                          <div key={lo.id} className="learning-object">
                            <div className="lo-header">
                              <span className="lo-icon">
                                {getLearningObjectTypeIcon(lo.object_type)}
                              </span>
                              <span className="lo-title">{lo.title}</span>
                              <span className="lo-type">{lo.object_type}</span>
                            </div>
                            {lo.content && (
                              <p className="lo-content">{lo.content}</p>
                            )}
                            {lo.keywords && lo.keywords.length > 0 && (
                              <div className="lo-keywords">
                                {lo.keywords.map((kw, i) => (
                                  <span key={i} className="keyword-tag">{kw}</span>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="no-los">No learning objects extracted for this section.</p>
                    )}

                    {section.content && (
                      <details className="raw-content">
                        <summary>View Raw Content</summary>
                        <pre>{section.content}</pre>
                      </details>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        <div className="content-stats">
          <div className="stat">
            <span className="stat-value">{sections.length}</span>
            <span className="stat-label">Sections</span>
          </div>
          <div className="stat">
            <span className="stat-value">
              {sections.reduce((acc, s) => acc + (s.learning_object_count || 0), 0)}
            </span>
            <span className="stat-label">Learning Objects</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ContentViewer;
