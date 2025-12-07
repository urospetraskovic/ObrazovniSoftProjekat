import React, { useRef } from 'react';

function FileUpload({ file, onFileSelect, onGenerate, loading }) {
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      const fileType = selectedFile.type;
      const fileName = selectedFile.name.toLowerCase();
      
      const isValidTxt = fileType === 'text/plain' || fileName.endsWith('.txt');
      const isValidPdf = fileType === 'application/pdf' || fileName.endsWith('.pdf');
      
      if (isValidTxt || isValidPdf) {
        onFileSelect(selectedFile);
      } else {
        alert('Please select a .txt or .pdf file');
      }
    }
  };

  return (
    <div className="card">
      <h2>📤 Upload Content</h2>
      <div className="upload-section">
        <div className="file-input-wrapper">
          <input
            ref={fileInputRef}
            type="file"
            accept=".txt,.pdf"
            onChange={handleFileChange}
            id="file-input"
          />
          <label
            htmlFor="file-input"
            className="file-input-label"
          >
            {file ? `✓ ${file.name}` : '📁 Click to select .txt or .pdf file'}
          </label>
        </div>

        {file && (
          <div className="file-info">
            <div><strong>File:</strong> {file.name}</div>
            <div><strong>Size:</strong> {(file.size / 1024).toFixed(2)} KB</div>
            <div><strong>Type:</strong> {file.type || 'document'}</div>
          </div>
        )}

        <div className="button-group">
          {file && (
            <button
              className="btn-secondary"
              onClick={() => onFileSelect(null)}
            >
              Clear
            </button>
          )}
          <button
            className="btn-primary"
            onClick={onGenerate}
            disabled={!file || loading}
          >
            {loading ? (
              <span className="loading">
                <span className="spinner"></span>
                Generating...
              </span>
            ) : (
              '🚀 Generate Quiz'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export default FileUpload;
