import React, { useState } from 'react';

function QuizConfig({ onApply, onCancel, loading }) {
  const [questionMode, setQuestionMode] = useState('auto'); // 'auto' or 'manual'
  const [totalQuestions, setTotalQuestions] = useState(10);
  const [useSmartChunking, setUseSmartChunking] = useState(true);
  const [distributionMode, setDistributionMode] = useState('auto'); // 'auto' or 'manual'
  const [distribution, setDistribution] = useState({
    prestructural: 20,
    unistructural: 20,
    multistructural: 30,
    relational: 20,
    extended_abstract: 10,
  });

  const handleDistributionChange = (level, value) => {
    setDistribution({
      ...distribution,
      [level]: parseInt(value) || 0,
    });
  };

  const getTotalPercentage = () => {
    return Object.values(distribution).reduce((a, b) => a + b, 0);
  };

  const handleApply = () => {
    if (distributionMode === 'manual') {
      const totalPct = getTotalPercentage();
      if (totalPct !== 100) {
        alert(`Distribution percentages must sum to 100% (currently ${totalPct}%)`);
        return;
      }
    }

    const config = {
      use_smart_chunking: useSmartChunking,
    };

    // Add question count config
    if (questionMode === 'auto') {
      config.total_questions = null; // Signal to model to decide
      config.question_mode = 'auto';
    } else {
      config.total_questions = totalQuestions;
      config.question_mode = 'manual';
    }

    // Add distribution config
    if (distributionMode === 'auto') {
      config.solo_distribution = null; // Signal to model to decide
      config.distribution_mode = 'auto';
    } else {
      config.solo_distribution = {
        prestructural: distribution.prestructural / 100,
        unistructural: distribution.unistructural / 100,
        multistructural: distribution.multistructural / 100,
        relational: distribution.relational / 100,
        extended_abstract: distribution.extended_abstract / 100,
      };
      config.distribution_mode = 'manual';
    }

    onApply(config);
  };

  const levelLabels = {
    prestructural: 'Prestructural (No understanding)',
    unistructural: 'Unistructural (Single aspect)',
    multistructural: 'Multistructural (Multiple aspects)',
    relational: 'Relational (Connections)',
    extended_abstract: 'Extended Abstract (Synthesis)',
  };

  const totalPct = getTotalPercentage();
  const isValidDistribution = distributionMode === 'auto' || totalPct === 100;

  return (
    <div className="quiz-config-overlay">
      <div className="quiz-config-modal">
        <h2>⚙️ Quiz Configuration</h2>

        <div className="config-section">
          <label>
            <strong>⚙️ Smart Content Chunking</strong>
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={useSmartChunking}
              onChange={(e) => setUseSmartChunking(e.target.checked)}
              disabled={loading}
            />
            <span>Use Smart Content Chunking</span>
          </label>
          <small>Automatically detects content sections (works with any format)</small>
        </div>

        <div className="config-section">
          <h3>❓ Number of Questions</h3>
          <div className="mode-selector">
            <label className="mode-option">
              <input
                type="radio"
                name="questionMode"
                value="auto"
                checked={questionMode === 'auto'}
                onChange={(e) => setQuestionMode(e.target.value)}
                disabled={loading}
              />
              <span className="mode-label">
                <strong>🤖 Let AI Decide</strong>
                <small>Model generates optimal number of questions</small>
              </span>
            </label>

            <label className="mode-option">
              <input
                type="radio"
                name="questionMode"
                value="manual"
                checked={questionMode === 'manual'}
                onChange={(e) => setQuestionMode(e.target.value)}
                disabled={loading}
              />
              <span className="mode-label">
                <strong>🎯 Custom Amount</strong>
                <small>You specify total questions</small>
              </span>
            </label>
          </div>

          {questionMode === 'manual' && (
            <div className="custom-input-section">
              <label>
                Total Questions to Generate
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={totalQuestions}
                  onChange={(e) => setTotalQuestions(parseInt(e.target.value) || 1)}
                  disabled={loading}
                />
              </label>
              <small>Questions will be distributed across chapters</small>
            </div>
          )}
        </div>

        <div className="config-section">
          <h3>📊 SOLO Level Distribution</h3>
          <div className="mode-selector">
            <label className="mode-option">
              <input
                type="radio"
                name="distributionMode"
                value="auto"
                checked={distributionMode === 'auto'}
                onChange={(e) => setDistributionMode(e.target.value)}
                disabled={loading}
              />
              <span className="mode-label">
                <strong>🤖 Let AI Decide</strong>
                <small>Model determines best SOLO level distribution</small>
              </span>
            </label>

            <label className="mode-option">
              <input
                type="radio"
                name="distributionMode"
                value="manual"
                checked={distributionMode === 'manual'}
                onChange={(e) => setDistributionMode(e.target.value)}
                disabled={loading}
              />
              <span className="mode-label">
                <strong>⚖️ Custom Distribution</strong>
                <small>You set percentage for each level</small>
              </span>
            </label>
          </div>

          {distributionMode === 'manual' && (
            <>
              <p style={{ fontSize: '0.9em', color: '#666', marginTop: '15px' }}>
                Adjust the percentage of questions for each SOLO taxonomy level:
              </p>

              <div className="distribution-grid">
                {Object.entries(distribution).map(([level, value]) => (
                  <div key={level} className="distribution-item">
                    <label htmlFor={level}>
                      <span className={`solo-badge solo-${level}`}>
                        {level.replace('_', ' ')}
                      </span>
                    </label>
                    <div className="input-group">
                      <input
                        id={level}
                        type="number"
                        min="0"
                        max="100"
                        value={value}
                        onChange={(e) =>
                          handleDistributionChange(level, e.target.value)
                        }
                        disabled={loading}
                      />
                      <span>%</span>
                    </div>
                  </div>
                ))}
              </div>

              <div
                className={`distribution-total ${
                  totalPct === 100 ? 'valid' : 'invalid'
                }`}
              >
                <strong>Total: {totalPct}%</strong>
                {totalPct !== 100 && (
                  <span className="warning">⚠️ Must equal 100%</span>
                )}
              </div>
            </>
          )}

          {distributionMode === 'auto' && (
            <div className="info-box">
              <p>
                The AI will analyze your content and generate questions distributed
                across SOLO levels based on the complexity and structure of the material.
              </p>
            </div>
          )}
        </div>

        <div className="config-info">
          <h4>💡 Quick Presets (Manual Mode)</h4>
          <div className="preset-buttons">
            <button
              className="preset-btn"
              onClick={() => {
                setDistribution({
                  prestructural: 20,
                  unistructural: 20,
                  multistructural: 30,
                  relational: 20,
                  extended_abstract: 10,
                });
              }}
            >
              Balanced
            </button>
            <button
              className="preset-btn"
              onClick={() => {
                setDistribution({
                  prestructural: 10,
                  unistructural: 10,
                  multistructural: 30,
                  relational: 30,
                  extended_abstract: 20,
                });
              }}
            >
              Advanced
            </button>
            <button
              className="preset-btn"
              onClick={() => {
                setDistribution({
                  prestructural: 30,
                  unistructural: 30,
                  multistructural: 25,
                  relational: 15,
                  extended_abstract: 0,
                });
              }}
            >
              Beginner
            </button>
          </div>
        </div>

        <div className="config-actions">
          <button
            className="btn-secondary"
            onClick={onCancel}
            disabled={loading}
          >
            Cancel
          </button>
          <button
            className="btn-primary"
            onClick={handleApply}
            disabled={loading || !isValidDistribution}
          >
            {loading ? 'Applying...' : 'Apply & Generate'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default QuizConfig;

