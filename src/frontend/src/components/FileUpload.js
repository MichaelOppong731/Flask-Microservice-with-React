import React, { useState } from 'react';
import axios from 'axios';

// Updated API endpoint for upload service
const UPLOAD_SERVICE_URL = 'http://localhost:8081';

function FileUpload({ user, token, userData, onFileUploaded }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState('');
  const isAuthenticated = userData && userData.authenticated === true;

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setMessage('');
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setMessage('Please select a file to upload.');
      return;
    }

    // Ensure user is authenticated
    if (!isAuthenticated) {
      setMessage('You need to be authenticated to upload files.');
      return;
    }

    setUploading(true);
    setMessage('');

    const formData = new FormData();
    formData.append('file', file);
    
    // Include user data in the request
    formData.append('user_data', JSON.stringify({
      username: user
    }));

    try {
      const headers = {
        'Content-Type': 'multipart/form-data',
      };
      
      // Add token if available
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await axios.post(`${UPLOAD_SERVICE_URL}/upload`, formData, {
        headers: headers,
      });

      setMessage('File uploaded successfully! Processing...');
      setFile(null);
      document.getElementById('file-input').value = '';
      
      // Get the video key from response
      const videoKey = response.data.video_key;
      
      onFileUploaded({
        videoKey: videoKey,
        audioKey: `${videoKey}.mp3`, // Predictable audio key
        name: file.name,
        uploadTime: new Date().toISOString(),
        status: 'processing'
      });
    } catch (err) {
      setMessage('Error uploading file. Please try again.');
      console.error('Upload error:', err);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="file-upload">
      <h3>Upload Video</h3>
      <form onSubmit={handleUpload} className="upload-form">
        <div className="form-group">
          <label htmlFor="file-input">Select Video File:</label>
          <input
            type="file"
            id="file-input"
            accept="video/*"
            onChange={handleFileChange}
            disabled={uploading}
          />
        </div>
        <button type="submit" disabled={uploading || !file}>
          {uploading ? 'Uploading...' : 'Upload and Convert'}
        </button>
      </form>
      {message && (
        <div className={`message ${message.includes('Error') ? 'error' : 'success'}`}>
          {message}
        </div>
      )}
    </div>
  );
}

export default FileUpload;
