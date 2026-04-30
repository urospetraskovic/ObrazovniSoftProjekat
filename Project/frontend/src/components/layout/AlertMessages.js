import React from 'react';

const ICONS = {
  warning: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  ),
  error: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10" />
      <line x1="15" y1="9" x2="9" y2="15" />
      <line x1="9" y1="9" x2="15" y2="15" />
    </svg>
  ),
  success: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
      <polyline points="22 4 12 14.01 9 11.01" />
    </svg>
  ),
};

function Alert({ kind, title, body, icon }) {
  return (
    <div className={`alert alert-${kind}`}>
      <div className="alert-icon">{icon}</div>
      <div className="alert-content">
        <strong>{title}</strong>
        <p>{body}</p>
      </div>
    </div>
  );
}

function AlertMessages({ apiStatus, error, success }) {
  return (
    <>
      {apiStatus?.api_exhausted && (
        <Alert
          kind="error"
          title="API Keys Exhausted!"
          body="All OpenRouter and GitHub Models keys have hit their daily limits. Please come back tomorrow or check your API quotas."
          icon={ICONS.warning}
        />
      )}
      {error && (
        <Alert kind="error" title="Error" body={error} icon={ICONS.error} />
      )}
      {success && (
        <Alert kind="success" title="Success" body={success} icon={ICONS.success} />
      )}
    </>
  );
}

export default AlertMessages;
