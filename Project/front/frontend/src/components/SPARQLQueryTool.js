import React, { useState, useEffect } from 'react';
import '../styles/SPARQLQueryTool.css';

function SPARQLQueryTool() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [examples, setExamples] = useState({});
  const [queryHistory, setQueryHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const rowsPerPage = 50;

  // Load example queries on component mount
  useEffect(() => {
    const fetchExamples = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/sparql/examples');
        const data = await response.json();
        setExamples(data);
      } catch (error) {
        console.error('Failed to load examples:', error);
      }
    };
    fetchExamples();
    
    // Load query history from localStorage
    const saved = localStorage.getItem('sparql_history');
    if (saved) {
      setQueryHistory(JSON.parse(saved));
    }
  }, []);

  const handleExecute = async () => {
    if (!query.trim()) {
      setResults({ error: 'Please enter a SPARQL query' });
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('http://localhost:5000/api/sparql', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        setResults({ error: data.error });
      } else {
        setResults(data);
        setCurrentPage(1); // Reset to first page on new results
        // Save to history
        const newHistory = [query, ...queryHistory.filter(q => q !== query)].slice(0, 10);
        setQueryHistory(newHistory);
        localStorage.setItem('sparql_history', JSON.stringify(newHistory));
      }
    } catch (error) {
      setResults({ error: `Connection error: ${error.message}` });
    }
    setLoading(false);
  };

  const loadExample = (exampleQuery) => {
    setQuery(exampleQuery);
  };

  const loadFromHistory = (historyQuery) => {
    setQuery(historyQuery);
  };

  const downloadResults = () => {
    if (!results || !results.results) return;
    
    const csv = convertToCSV(results.results, results.variables);
    const element = document.createElement('a');
    element.setAttribute('href', 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv));
    element.setAttribute('download', `sparql_results_${Date.now()}.csv`);
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const convertToCSV = (data, headers) => {
    if (!data || data.length === 0) return 'No data';
    
    const csvHeaders = headers.join(',');
    const csvRows = data.map(row => 
      headers.map(header => {
        const value = row[header] || '';
        // Escape quotes and wrap in quotes if contains comma
        return `"${String(value).replace(/"/g, '""')}"`;
      }).join(',')
    );
    
    return [csvHeaders, ...csvRows].join('\n');
  };

  // Pagination logic
  const getPaginatedResults = () => {
    if (!results || !results.results) return { items: [], totalPages: 0 };
    
    const totalItems = results.results.length;
    const totalPages = Math.ceil(totalItems / rowsPerPage);
    const startIdx = (currentPage - 1) * rowsPerPage;
    const endIdx = startIdx + rowsPerPage;
    const items = results.results.slice(startIdx, endIdx);
    
    return { items, totalPages, totalItems, startIdx, endIdx };
  };

  const handlePrevPage = () => {
    setCurrentPage(prev => Math.max(1, prev - 1));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleNextPage = () => {
    const { totalPages } = getPaginatedResults();
    setCurrentPage(prev => Math.min(totalPages, prev + 1));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="sparql-container">
      <div className="sparql-header">
        <h2>🔍 SPARQL Query Tool</h2>
        <p>Query your OS ontology with SPARQL</p>
      </div>

      <div className="sparql-content">
        {/* Examples Section */}
        <div className="sparql-section examples-section">
          <h3>📚 Example Queries</h3>
          <div className="examples-grid">
            {Object.entries(examples).map(([key, ex]) => (
              <button
                key={key}
                className="example-btn"
                onClick={() => loadExample(ex.query)}
                title={ex.title}
              >
                {ex.title}
              </button>
            ))}
          </div>
        </div>

        {/* Query Editor Section */}
        <div className="sparql-section editor-section">
          <h3>✏️ Write Your Query</h3>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter SPARQL query here..."
            className="query-textarea"
            spellCheck="false"
          />
          
          <div className="editor-controls">
            <button
              onClick={handleExecute}
              disabled={loading || !query.trim()}
              className="execute-btn"
            >
              {loading ? '⏳ Executing...' : '▶️ Execute Query'}
            </button>
            <button
              onClick={() => setQuery('')}
              className="clear-btn"
            >
              🗑️ Clear
            </button>
          </div>
        </div>

        {/* Query History */}
        {queryHistory.length > 0 && (
          <div className="sparql-section history-section">
            <div className="history-header">
              <h3>📋 Query History</h3>
              <button
                onClick={() => setShowHistory(!showHistory)}
                className="toggle-history-btn"
                title={showHistory ? "Hide history" : "Show history"}
              >
                {showHistory ? '▼ Hide' : '▶ Show'}
              </button>
            </div>
            {showHistory && (
              <div className="history-list">
                {queryHistory.map((q, idx) => (
                  <button
                    key={idx}
                    className="history-btn"
                    onClick={() => loadFromHistory(q)}
                    title={q}
                  >
                    {q.substring(0, 50)}...
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Results Section */}
      {results && (
        <div className="sparql-section results-section">
          <div className="results-header">
            <h3>📊 Results</h3>
            {results.count !== undefined && (
              <span className="result-count">{results.count} rows</span>
            )}
            {results.results && results.results.length > 0 && (
              <button onClick={downloadResults} className="download-btn">
                ⬇️ Download CSV
              </button>
            )}
          </div>

          {results.error ? (
            <div className="error-box">
              <strong>❌ Error:</strong>
              <pre>{results.error}</pre>
            </div>
          ) : results.results && results.results.length > 0 ? (
            <>
              {/* Top Pagination Controls */}
              {(() => {
                const { totalPages, totalItems, startIdx, endIdx } = getPaginatedResults();
                if (totalPages > 1) {
                  return (
                    <div className="pagination-controls">
                      <button
                        onClick={handlePrevPage}
                        disabled={currentPage === 1}
                        className="pagination-btn"
                      >
                        ◀ Previous
                      </button>
                      
                      <span className="pagination-info">
                        Showing {startIdx + 1} - {Math.min(endIdx, totalItems)} of {totalItems} 
                        (Page {currentPage} of {totalPages})
                      </span>
                      
                      <button
                        onClick={handleNextPage}
                        disabled={currentPage === totalPages}
                        className="pagination-btn"
                      >
                        Next ▶
                      </button>
                    </div>
                  );
                }
                return null;
              })()}

              <div className="results-table-wrapper">
                <table className="results-table">
                  <thead>
                    <tr>
                      {results.variables && results.variables.map((variable) => (
                        <th key={variable}>{variable}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {getPaginatedResults().items.map((row, idx) => (
                      <tr key={idx}>
                        {results.variables && results.variables.map((variable) => (
                          <td key={`${idx}-${variable}`} className="result-cell">
                            {renderCellValue(row[variable])}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              {/* Pagination Controls */}
              {(() => {
                const { totalPages, totalItems, startIdx, endIdx } = getPaginatedResults();
                if (totalPages > 1) {
                  return (
                    <div className="pagination-controls">
                      <button
                        onClick={handlePrevPage}
                        disabled={currentPage === 1}
                        className="pagination-btn"
                      >
                        ◀ Previous
                      </button>
                      
                      <span className="pagination-info">
                        Showing {startIdx + 1} - {Math.min(endIdx, totalItems)} of {totalItems} 
                        (Page {currentPage} of {totalPages})
                      </span>
                      
                      <button
                        onClick={handleNextPage}
                        disabled={currentPage === totalPages}
                        className="pagination-btn"
                      >
                        Next ▶
                      </button>
                    </div>
                  );
                }
                return null;
              })()}
            </>
          ) : (
            <div className="empty-box">
              <p>✅ Query executed successfully, but no results found.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Helper to render cell values (truncate URIs, format nicely)
function renderCellValue(value) {
  if (!value) return '—';
  
  const str = String(value);
  
  // If it's a URI, extract the last part
  if (str.includes('/') && str.includes('#')) {
    return str.split('#').pop() || str;
  } else if (str.includes('/')) {
    return str.split('/').pop() || str;
  }
  
  // Truncate long strings
  if (str.length > 100) {
    return <span title={str}>{str.substring(0, 100)}...</span>;
  }
  
  return str;
}

export default SPARQLQueryTool;
