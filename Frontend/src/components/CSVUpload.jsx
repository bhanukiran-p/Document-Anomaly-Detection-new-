import React, { useState, useRef } from 'react';
import { colors } from '../styles/colors';

const CSVUpload = () => {
  const [file, setFile] = useState(null);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const fileInputRef = useRef(null);

  const primary = colors.primaryColor || '#E53935';

  const dragDropStyle = {
    border: `2px dashed ${colors.border}`,
    borderRadius: '0.75rem',
    padding: '3rem',
    textAlign: 'center',
    cursor: 'pointer',
    transition: 'all 0.3s',
    backgroundColor: colors.muted,
  };

  const dragDropActiveStyle = {
    ...dragDropStyle,
    borderColor: primary,
    backgroundColor: `${primary}10`,
  };

  const fileInfoStyle = {
    marginTop: '1.5rem',
    padding: '1rem',
    backgroundColor: colors.background,
    borderRadius: '0.5rem',
    border: `1px solid ${colors.border}`,
  };

  const fileNameStyle = {
    color: colors.foreground,
    fontWeight: '600',
    marginBottom: '0.5rem',
  };

  const fileSizeStyle = {
    color: colors.mutedForeground,
    fontSize: '0.9rem',
  };

  const buttonStyle = {
    backgroundColor: primary,
    color: '#fff',
    padding: '0.75rem 1.5rem',
    borderRadius: '0.5rem',
    fontSize: '1rem',
    fontWeight: '600',
    border: 'none',
    cursor: 'pointer',
    transition: 'all 0.3s',
    boxShadow: `0 0 20px ${primary}40`,
    marginTop: '1rem',
  };

  const messageStyle = (type) => ({
    borderRadius: '0.5rem',
    padding: '1rem',
    marginTop: '1rem',
    fontSize: '0.95rem',
    backgroundColor: type === 'error' ? 'rgba(244, 67, 54, 0.1)' : 'rgba(16, 185, 129, 0.1)',
    border: `1px solid ${type === 'error' ? '#F44336' : '#10b981'}`,
    color: type === 'error' ? '#FF6B6B' : '#10b981',
  });

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleFileSelect = (selectedFile) => {
    setError(null);
    setSuccess(null);

    if (!selectedFile.name.endsWith('.csv')) {
      setError('Please select a valid CSV file');
      return;
    }

    if (selectedFile.size > 10 * 1024 * 1024) {
      setError('File size must be less than 10MB');
      return;
    }

    setFile(selectedFile);
  };

  const handleFileInputChange = (e) => {
    if (e.target.files.length > 0) {
      handleFileSelect(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const content = await file.text();
      const lines = content.trim().split('\n');

      if (lines.length === 0) throw new Error('CSV file is empty');

      const headers = lines[0].split(',').map((h) => h.trim());
      const recordCount = lines.length - 1;

      setSuccess(
        `Successfully uploaded! Found ${recordCount} records with ${headers.length} columns.`
      );
      setFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (err) {
      setError(err.message || 'Failed to parse CSV file');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClear = () => {
    setFile(null);
    setError(null);
    setSuccess(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div>
      <div
        style={file ? dragDropStyle : dragDropActiveStyle}
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDrop={!file ? handleDrop : undefined}
        onClick={() => !file && fileInputRef.current?.click()}
      >
        {!file ? (
          <>
            <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>📁</div>
            <p style={{ color: colors.foreground, marginBottom: '0.5rem' }}>
              Drag and drop your CSV file here
            </p>
            <p style={{ color: colors.mutedForeground, fontSize: '0.9rem' }}>
              or click to browse (Max 10MB)
            </p>
          </>
        ) : (
          <>
            <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>✓</div>
            <p style={{ color: colors.foreground }}>File ready for upload</p>
          </>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          onChange={handleFileInputChange}
          style={{ display: 'none' }}
        />
      </div>

      {file && (
        <div style={fileInfoStyle}>
          <div style={fileNameStyle}>{file.name}</div>
          <div style={fileSizeStyle}>
            Size: {(file.size / 1024).toFixed(2)} KB
          </div>
        </div>
      )}

      {file && (
        <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
          <button
            style={{ ...buttonStyle, flex: 1 }}
            onMouseEnter={(e) => {
              e.target.style.transform = 'translateY(-2px)';
              e.target.style.boxShadow = `0 6px 30px ${primary}60`;
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = 'translateY(0)';
              e.target.style.boxShadow = `0 0 20px ${primary}40`;
            }}
            onClick={handleUpload}
            disabled={isLoading}
          >
            {isLoading ? 'Processing...' : 'Upload CSV'}
          </button>
          <button
            style={{
              ...buttonStyle,
              backgroundColor: colors.muted,
              color: colors.foreground,
              boxShadow: 'none',
              flex: 1,
            }}
            onMouseEnter={(e) => {
              e.target.style.backgroundColor = colors.border;
            }}
            onMouseLeave={(e) => {
              e.target.style.backgroundColor = colors.muted;
            }}
            onClick={handleClear}
            disabled={isLoading}
          >
            Clear
          </button>
        </div>
      )}

      {error && <div style={messageStyle('error')}>{error}</div>}
      {success && <div style={messageStyle('success')}>{success}</div>}
    </div>
  );
};

export default CSVUpload;
