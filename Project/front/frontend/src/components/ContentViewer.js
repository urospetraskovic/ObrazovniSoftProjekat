import React, { useState, useEffect } from 'react';
import { lessonApi, sectionApi, learningObjectApi } from '../api';

function ContentViewer({ lesson, onBack, onSuccess, onError, onLessonUpdate }) {
  const [sections, setSections] = useState([]);
  const [expandedSection, setExpandedSection] = useState(null);
  const [loading, setLoading] = useState(false);
  const [ontology, setOntology] = useState([]);
  const [showOntology, setShowOntology] = useState(false);
  const [editingLO, setEditingLO] = useState(null);
  const [editFormData, setEditFormData] = useState({});
  const [showEditModal, setShowEditModal] = useState(false);

  useEffect(() => {
    if (lesson?.sections) {
      setSections(lesson.sections);
    } else {
      fetchSections();
    }
    
    if (lesson?.id) {
      fetchOntology();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lesson]);

  const fetchSections = async () => {
    if (!lesson?.id) return;
    
    try {
      setLoading(true);
      const response = await lessonApi.getSections(lesson.id);
      setSections(response.data.sections || []);
    } catch (err) {
      onError('Failed to fetch sections');
    } finally {
      setLoading(false);
    }
  };

  const fetchOntology = async () => {
    if (!lesson?.id) return;
    try {
      const response = await lessonApi.getOntology(lesson.id);
      setOntology(response.data.relationships || []);
    } catch (err) {
      // Silent failure for ontology fetch
    }
  };

  const fetchLearningObjects = async (sectionId) => {
    try {
      const response = await sectionApi.getById(sectionId);
      const updatedSection = response.data.section;
      
      setSections(sections.map(s => 
        s.id === sectionId ? { ...s, learning_objects: updatedSection.learning_objects } : s
      ));
    } catch (err) {
      // Silent failure for learning objects fetch
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

  const handleEditLO = (lo) => {
    setEditingLO(lo);
    setEditFormData({
      title: lo.title,
      content: lo.content,
      object_type: lo.object_type,
      keywords: lo.keywords ? lo.keywords.join(', ') : ''
    });
    setShowEditModal(true);
  };

  const handleUpdateLO = async () => {
    if (!editingLO) return;
    
    try {
      const keywordsArray = editFormData.keywords
        ? editFormData.keywords.split(',').map(k => k.trim()).filter(k => k)
        : [];
      
      const response = await learningObjectApi.update(editingLO.id, {
        title: editFormData.title,
        content: editFormData.content,
        object_type: editFormData.object_type,
        keywords: keywordsArray
      });
      
      // Update sections with new learning object data
      setSections(sections.map(s => ({
        ...s,
        learning_objects: s.learning_objects.map(lo =>
          lo.id === editingLO.id ? response.data.learning_object : lo
        )
      })));
      
      setShowEditModal(false);
      setEditingLO(null);
      onSuccess('Learning object updated successfully');
    } catch (err) {
      onError(err.response?.data?.error || 'Failed to update learning object');
    }
  };

  const handleDeleteLO = async (loId, loTitle) => {
    if (!window.confirm(`Are you sure you want to delete "${loTitle}"?`)) {
      return;
    }
    
    try {
      await learningObjectApi.delete(loId);
      
      // Remove from sections
      setSections(sections.map(s => ({
        ...s,
        learning_objects: s.learning_objects.filter(lo => lo.id !== loId),
        learning_object_count: (s.learning_object_count || 1) - 1
      })));
      
      onSuccess('Learning object deleted successfully');
    } catch (err) {
      onError(err.response?.data?.error || 'Failed to delete learning object');
    }
  };

  const handleParseLesson = async () => {
    try {
      setLoading(true);
      const response = await lessonApi.parse(lesson.id);
      
      const { sections: newSections, section_count, learning_object_count, ontology_relationships } = response.data;
      setSections(newSections || []);
      onSuccess(`Parsed ${section_count} sections with ${learning_object_count} learning objects and ${ontology_relationships} ontology relationships!`);
      
      // Refresh ontology
      fetchOntology();
      
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

        {/* Domain Ontology Section */}
        {sections.length > 0 && (
          <div className="ontology-section" style={{ padding: '20px', borderTop: '1px solid var(--neutral-200)', background: 'var(--neutral-50)' }}>
            <div 
              style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
              onClick={() => setShowOntology(!showOntology)}
            >
              <h4 style={{ margin: 0 }}>🕸️ Domain Ontology</h4>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span className="badge" style={{ background: 'var(--primary-100)', color: 'var(--primary-700)', padding: '2px 8px', borderRadius: '10px', fontSize: '0.8rem' }}>
                  {ontology.length} Relationships
                </span>
                <span>{showOntology ? '▼' : '▶'}</span>
              </div>
            </div>

            {showOntology && (
              <div className="ontology-content" style={{ marginTop: '20px' }}>
                {ontology.length > 0 ? (
                  <div className="ontology-table-container" style={{ 
                    overflowX: 'auto', 
                    background: 'white', 
                    borderRadius: '12px', 
                    border: '1px solid var(--neutral-200)',
                    boxShadow: 'var(--shadow-sm)'
                  }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                      <thead>
                        <tr style={{ background: 'var(--neutral-50)', borderBottom: '2px solid var(--neutral-200)' }}>
                          <th style={{ padding: '12px 20px', fontSize: '0.85rem', color: 'var(--neutral-600)', fontWeight: '600' }}>Source Concept</th>
                          <th style={{ padding: '12px 20px', fontSize: '0.85rem', color: 'var(--neutral-600)', fontWeight: '600', textAlign: 'center' }}>Relationship</th>
                          <th style={{ padding: '12px 20px', fontSize: '0.85rem', color: 'var(--neutral-600)', fontWeight: '600' }}>Target Concept</th>
                        </tr>
                      </thead>
                      <tbody>
                        {ontology.map((rel, idx) => (
                          <tr key={idx} style={{ borderBottom: idx === ontology.length - 1 ? 'none' : '1px solid var(--neutral-100)' }}>
                            <td style={{ padding: '15px 20px', fontWeight: '600', color: 'var(--neutral-800)' }}>
                              {rel.source_title}
                            </td>
                            <td style={{ padding: '15px 20px', textAlign: 'center' }}>
                              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
                                <span style={{ 
                                  fontSize: '0.7rem', 
                                  fontWeight: '800', 
                                  textTransform: 'uppercase', 
                                  color: 'var(--primary-600)',
                                  background: 'var(--primary-50)',
                                  padding: '2px 8px',
                                  borderRadius: '4px',
                                  border: '1px solid var(--primary-100)',
                                  whiteSpace: 'nowrap'
                                }}>
                                  {rel.relationship_type.replace('_', ' ')}
                                </span>
                                <span style={{ color: 'var(--neutral-400)', fontSize: '1.2rem', lineHeight: '1' }}>⟶</span>
                                {rel.description && (
                                  <span style={{ fontSize: '0.75rem', color: 'var(--neutral-500)', fontStyle: 'italic', maxWidth: '200px' }}>
                                    {rel.description}
                                  </span>
                                )}
                              </div>
                            </td>
                            <td style={{ padding: '15px 20px', fontWeight: '600', color: 'var(--neutral-800)' }}>
                              {rel.target_title}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div style={{ padding: '40px', textAlign: 'center', background: 'white', borderRadius: '12px', border: '1px dashed var(--neutral-300)' }}>
                    <p style={{ color: 'var(--neutral-500)', margin: 0 }}>No ontology relationships identified yet. Parse the lesson to generate them.</p>
                  </div>
                )}
              </div>
            )}
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
                      <span className="page-range" style={{ marginLeft: '12px', color: 'var(--neutral-500)', fontSize: '0.85rem' }}>
                        Pages {section.start_page}-{section.end_page}
                      </span>
                    )}
                  </div>
                  <div className="section-meta" style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                    <span className="lo-count" style={{ 
                      background: 'var(--neutral-100)', 
                      padding: '2px 10px', 
                      borderRadius: '12px', 
                      fontSize: '0.8rem',
                      color: 'var(--neutral-600)',
                      fontWeight: '500'
                    }}>
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
                              {/* AI Generation Status Badge */}
                              <span className={`lo-status-badge ${lo.human_modified ? 'human-modified' : lo.is_ai_generated ? 'ai-generated' : 'human-created'}`}>
                                {lo.human_modified ? '⚠️ Human Modified' : lo.is_ai_generated ? '🤖 AI Generated' : '👤 Human Created'}
                              </span>
                              {/* Action Buttons */}
                              <button 
                                className="btn-icon btn-edit"
                                onClick={() => handleEditLO(lo)}
                                title="Edit"
                              >
                                ✏️
                              </button>
                              <button 
                                className="btn-icon btn-delete"
                                onClick={() => handleDeleteLO(lo.id, lo.title)}
                                title="Delete"
                              >
                                🗑️
                              </button>
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

      {/* Edit Learning Object Modal */}
      {showEditModal && editingLO && (
        <div className="modal-overlay" onClick={() => setShowEditModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Edit Learning Object</h3>
              <button 
                className="btn-close" 
                onClick={() => setShowEditModal(false)}
              >
                ✕
              </button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>Title</label>
                <input
                  type="text"
                  value={editFormData.title || ''}
                  onChange={(e) => setEditFormData({...editFormData, title: e.target.value})}
                  placeholder="Learning object title"
                />
              </div>
              <div className="form-group">
                <label>Type</label>
                <select
                  value={editFormData.object_type || ''}
                  onChange={(e) => setEditFormData({...editFormData, object_type: e.target.value})}
                >
                  <option value="">Select type...</option>
                  <option value="concept">Concept</option>
                  <option value="definition">Definition</option>
                  <option value="procedure">Procedure</option>
                  <option value="principle">Principle</option>
                  <option value="example">Example</option>
                  <option value="fact">Fact</option>
                </select>
              </div>
              <div className="form-group">
                <label>Content</label>
                <textarea
                  value={editFormData.content || ''}
                  onChange={(e) => setEditFormData({...editFormData, content: e.target.value})}
                  placeholder="Learning object content"
                  rows="6"
                />
              </div>
              <div className="form-group">
                <label>Keywords (comma-separated)</label>
                <input
                  type="text"
                  value={editFormData.keywords || ''}
                  onChange={(e) => setEditFormData({...editFormData, keywords: e.target.value})}
                  placeholder="keyword1, keyword2, keyword3"
                />
              </div>
            </div>
            <div className="modal-footer">
              <button 
                className="btn-secondary" 
                onClick={() => setShowEditModal(false)}
              >
                Cancel
              </button>
              <button 
                className="btn-primary" 
                onClick={handleUpdateLO}
              >
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ContentViewer;
