import React from 'react';

function HowItWorksCard() {
  return (
    <div className="info-card" style={{ marginTop: '40px' }}>
      <h3>How It Works</h3>
      <ol>
        <li><strong>Create Course:</strong> Start by creating a course (e.g., "Operating Systems")</li>
        <li><strong>Upload Lessons:</strong> Add PDF lessons to your course</li>
        <li><strong>Parse Content:</strong> AI extracts sections and learning objects from lessons</li>
        <li><strong>Generate Questions:</strong> Create SOLO-based questions from your content</li>
        <li><strong>Build Quiz:</strong> Combine questions into quizzes and download as JSON</li>
      </ol>
      <div className="solo-levels">
        <h4>SOLO Taxonomy Levels:</h4>
        <ul>
          <li><strong>Unistructural:</strong> Single fact recall (from lesson)</li>
          <li><strong>Multistructural:</strong> Multiple related facts (from sections)</li>
          <li><strong>Relational:</strong> Analyze relationships (from learning objects)</li>
          <li><strong>Extended Abstract:</strong> Combine knowledge (from 2+ lessons)</li>
        </ul>
      </div>
    </div>
  );
}

export default HowItWorksCard;
