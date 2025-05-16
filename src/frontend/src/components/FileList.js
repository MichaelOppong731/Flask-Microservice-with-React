import React, { useState } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_DOWNLOAD_SERVICE_URL || 'http://localhost:8082';

function FileList({ user, token, userData, files, onFileDeleted }) {
  const [downloading, setDownloading] = useState({});
  const isAuthenticated = userData && userData.authenticated === true;

  const handleDownload = async (file) => {
    // Ensure user is authenticated
    if (!isAuthenticated) {
      alert('You need to be authenticated to download files.');
      return;
    }
    
    const audioKey = file.audioKey;
    
    if (!audioKey) {
      alert('Audio file not ready yet or audio key missing.');
      return;
    }

    setDownloading(prev => ({ ...prev, [audioKey]: true }));
    
    try {
      const config = {
        responseType: 'blob',
      };
      
      let url = `${API_BASE_URL}/download?fid=${audioKey}`;
      
      // Add authorization header if token is available
      if (token) {
        config.headers = {
          'Authorization': `Bearer ${token}`
        };
      }
      
      const response = await axios.get(url, config);

      const downloadUrl = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.setAttribute('download', `${file.name}.mp3`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);
    } catch (err) {
      console.error('Download error:', err);
      alert('Error downloading file. File may not be ready yet.');
    } finally {
      setDownloading(prev => ({ ...prev, [audioKey]: false }));
    }
  };

  const handleDelete = (file) => {
    // Ensure user is authenticated
    if (!isAuthenticated) {
      alert('You need to be authenticated to remove files.');
      return;
    }
    
    if (window.confirm(`Are you sure you want to remove "${file.name}" from the list?`)) {
      // Just remove from frontend, don't delete from S3
      onFileDeleted(file.videoKey);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'processing':
        return '⏳';
      case 'completed':
        return '✅';
      case 'error':
        return '❌';
      default:
        return '📄';
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="file-list">
        <h3>Your Files</h3>
        <p>You need to be authenticated to view files.</p>
      </div>
    );
  }

  return (
    <div className="file-list">
      <h3>Your Files</h3>
      {files.length === 0 ? (
        <p>No files uploaded yet.</p>
      ) : (
        <div className="files-grid">
          {files.map((file, index) => (
            <div key={file.videoKey || index} className="file-card">
              <div className="file-card-header">
                <h4>{file.name}</h4>
                <button
                  className="delete-btn"
                  onClick={() => handleDelete(file)}
                  title="Remove from list"
                >
                  <span className="delete-icon">×</span>
                </button>
              </div>
              <p>
                {getStatusIcon(file.status)} Status: {file.status}
              </p>
              <p>Uploaded: {new Date(file.uploadTime).toLocaleDateString()}</p>
              {file.status === 'completed' && file.audioKey && (
                <button 
                  onClick={() => handleDownload(file)}
                  className="download-btn"
                  disabled={downloading[file.audioKey]}
                >
                  {downloading[file.audioKey] ? 'Downloading...' : 'Download MP3'}
                </button>
              )}
              {file.status === 'processing' && (
                <div className="processing-indicator">
                  <div className="spinner"></div>
                  <span>Converting...</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default FileList;
