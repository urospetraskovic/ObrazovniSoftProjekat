import React, { useState } from 'react';
import { questionApi } from '../api';

function ManualQuestionAdder({ courseId, lessons, onSuccess, onError, onRefresh }) {
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    question_text: '',
    solo_level: 'unistructural',
    question_type: 'multiple_choice',
    primary_lesson_id: lessons && lessons.length > 0 ? lessons[0].id : null,
    secondary_lesson_id: lessons && lessons.length > 1 ? lessons[1].id : null,
    options: ['', '', '', ''],
    correct_option_index: 0,
    correct_answer: '',
    explanation: '',
    difficulty: 0.5,
    bloom_level: 'remember',
    tags: ''
  });

  const soloLevels = [
    { value: 'unistructural', label: 'Unistructural' },
    { value: 'multistructural', label: 'Multistructural' },
    { value: 'relational', label: 'Relational' },
    { value: 'extended_abstract', label: 'Extended Abstract' }
  ];

  const questionTypes = [
    { value: 'multiple_choice', label: 'Multiple Choice' },
    { value: 'true_false', label: 'True/False' },
    { value: 'short_answer', label: 'Short Answer' }
  ];

  const bloomLevels = [
    'remember', 'understand', 'apply', 'analyze', 'evaluate', 'create'
  ];

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleOptionChange = (index, value) => {
    const newOptions = [...formData.options];
    newOptions[index] = value;
    setFormData(prev => ({
      ...prev,
      options: newOptions
    }));
  };

  const addOption = () => {
    setFormData(prev => ({
      ...prev,
      options: [...prev.options, '']
    }));
  };

  const removeOption = (index) => {
    if (formData.options.length > 2) {
      setFormData(prev => ({
        ...prev,
        options: prev.options.filter((_, i) => i !== index)
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Validate required fields
      if (!formData.question_text.trim()) {
        onError('Question text is required');
        setLoading(false);
        return;
      }

      // Prepare question data
      const questionData = {
        question_text: formData.question_text,
        solo_level: formData.solo_level,
        question_type: formData.question_type,
        primary_lesson_id: formData.primary_lesson_id || null,
        secondary_lesson_id: formData.question_type === 'extended_abstract' ? formData.secondary_lesson_id : null,
        explanation: formData.explanation || null,
        difficulty: parseFloat(formData.difficulty) || null,
        bloom_level: formData.bloom_level || null,
        tags: formData.tags ? formData.tags.split(',').map(t => t.trim()).filter(t => t) : []
      };

      // Add question type specific fields
      if (formData.question_type === 'multiple_choice') {
        // Filter out empty options
        const validOptions = formData.options.filter(opt => opt.trim());
        if (validOptions.length < 2) {
          onError('Multiple choice questions need at least 2 options');
          setLoading(false);
          return;
        }
        questionData.options = validOptions;
        if (formData.correct_option_index >= validOptions.length) {
          onError('Correct answer index is invalid');
          setLoading(false);
          return;
        }
        questionData.correct_option_index = formData.correct_option_index;
        questionData.correct_answer = validOptions[formData.correct_option_index];
      } else if (formData.question_type === 'true_false') {
        questionData.options = ['True', 'False'];
        questionData.correct_answer = formData.correct_answer || 'True';
        questionData.correct_option_index = questionData.options.indexOf(questionData.correct_answer);
      } else if (formData.question_type === 'short_answer') {
        questionData.correct_answer = formData.correct_answer;
      }

      // Create question
      await questionApi.create(questionData);

      // Reset form
      setFormData({
        question_text: '',
        solo_level: 'unistructural',
        question_type: 'multiple_choice',
        primary_lesson_id: lessons && lessons.length > 0 ? lessons[0].id : null,
        secondary_lesson_id: lessons && lessons.length > 1 ? lessons[1].id : null,
        options: ['', '', '', ''],
        correct_option_index: 0,
        correct_answer: '',
        explanation: '',
        difficulty: 0.5,
        bloom_level: 'remember',
        tags: ''
      });

      setShowForm(false);
      onSuccess('Question added successfully!');
      if (onRefresh) {
        onRefresh();
      }
    } catch (err) {
      onError(err.response?.data?.error || 'Failed to create question');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="manual-question-adder">
      <button 
        className="btn-primary"
        onClick={() => setShowForm(!showForm)}
      >
        {showForm ? 'Cancel' : '+ Add Manual Question'}
      </button>

      {showForm && (
        <div className="add-question-form-container">
          <form onSubmit={handleSubmit} className="add-question-form">
            <h3>Add Manual Question</h3>

            {/* Question Text */}
            <div className="form-group">
              <label>Question Text *</label>
              <textarea
                name="question_text"
                value={formData.question_text}
                onChange={handleInputChange}
                placeholder="Enter your question..."
                rows="3"
                required
              />
            </div>

            {/* SOLO Level */}
            <div className="form-row">
              <div className="form-group">
                <label>SOLO Level *</label>
                <select
                  name="solo_level"
                  value={formData.solo_level}
                  onChange={handleInputChange}
                >
                  {soloLevels.map(level => (
                    <option key={level.value} value={level.value}>
                      {level.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Question Type */}
              <div className="form-group">
                <label>Question Type *</label>
                <select
                  name="question_type"
                  value={formData.question_type}
                  onChange={handleInputChange}
                >
                  {questionTypes.map(type => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Lesson Selection */}
            <div className="form-row">
              <div className="form-group">
                <label>Primary Lesson</label>
                <select
                  name="primary_lesson_id"
                  value={formData.primary_lesson_id || ''}
                  onChange={handleInputChange}
                >
                  <option value="">Select a lesson...</option>
                  {lessons && lessons.map(lesson => (
                    <option key={lesson.id} value={lesson.id}>
                      {lesson.title}
                    </option>
                  ))}
                </select>
              </div>

              {formData.solo_level === 'extended_abstract' && (
                <div className="form-group">
                  <label>Secondary Lesson (for comparison)</label>
                  <select
                    name="secondary_lesson_id"
                    value={formData.secondary_lesson_id || ''}
                    onChange={handleInputChange}
                  >
                    <option value="">Select a lesson...</option>
                    {lessons && lessons.map(lesson => (
                      <option key={lesson.id} value={lesson.id}>
                        {lesson.title}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>

            {/* Question Type Specific Fields */}
            {formData.question_type === 'multiple_choice' && (
              <div className="form-group">
                <label>Options</label>
                {formData.options.map((option, index) => (
                  <div key={index} className="option-input-group">
                    <input
                      type="radio"
                      name="correct_option"
                      checked={formData.correct_option_index === index}
                      onChange={() => setFormData(prev => ({...prev, correct_option_index: index}))}
                    />
                    <input
                      type="text"
                      value={option}
                      onChange={(e) => handleOptionChange(index, e.target.value)}
                      placeholder={`Option ${index + 1}`}
                    />
                    {formData.options.length > 2 && (
                      <button
                        type="button"
                        onClick={() => removeOption(index)}
                        className="btn-icon btn-remove"
                      >
                        ✕
                      </button>
                    )}
                  </div>
                ))}
                <button
                  type="button"
                  onClick={addOption}
                  className="btn-secondary"
                  style={{ marginTop: '10px' }}
                >
                  + Add Option
                </button>
              </div>
            )}

            {formData.question_type === 'true_false' && (
              <div className="form-group">
                <label>Correct Answer</label>
                <div className="true-false-options">
                  <label>
                    <input
                      type="radio"
                      name="correct_answer"
                      value="True"
                      checked={formData.correct_answer === 'True'}
                      onChange={handleInputChange}
                    />
                    True
                  </label>
                  <label>
                    <input
                      type="radio"
                      name="correct_answer"
                      value="False"
                      checked={formData.correct_answer === 'False'}
                      onChange={handleInputChange}
                    />
                    False
                  </label>
                </div>
              </div>
            )}

            {formData.question_type === 'short_answer' && (
              <div className="form-group">
                <label>Expected Answer</label>
                <input
                  type="text"
                  name="correct_answer"
                  value={formData.correct_answer}
                  onChange={handleInputChange}
                  placeholder="Enter the expected answer..."
                />
              </div>
            )}

            {/* Explanation */}
            <div className="form-group">
              <label>Explanation (optional)</label>
              <textarea
                name="explanation"
                value={formData.explanation}
                onChange={handleInputChange}
                placeholder="Provide an explanation for the correct answer..."
                rows="3"
              />
            </div>

            {/* Difficulty & Bloom Level */}
            <div className="form-row">
              <div className="form-group">
                <label>Difficulty (0-1)</label>
                <input
                  type="number"
                  name="difficulty"
                  min="0"
                  max="1"
                  step="0.1"
                  value={formData.difficulty}
                  onChange={handleInputChange}
                />
              </div>

              <div className="form-group">
                <label>Bloom's Level</label>
                <select
                  name="bloom_level"
                  value={formData.bloom_level}
                  onChange={handleInputChange}
                >
                  {bloomLevels.map(level => (
                    <option key={level} value={level}>
                      {level.charAt(0).toUpperCase() + level.slice(1)}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Tags */}
            <div className="form-group">
              <label>Tags (comma-separated)</label>
              <input
                type="text"
                name="tags"
                value={formData.tags}
                onChange={handleInputChange}
                placeholder="tag1, tag2, tag3"
              />
            </div>

            {/* Status Badge */}
            <div className="form-status-info">
              <span className="status-badge human-created">
                This will be marked as: Human Created
              </span>
            </div>

            {/* Form Actions */}
            <div className="form-actions">
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn-primary"
                disabled={loading}
              >
                {loading ? 'Adding...' : 'Add Question'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

export default ManualQuestionAdder;
