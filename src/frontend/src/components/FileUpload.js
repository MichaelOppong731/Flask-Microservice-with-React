import React, { useState } from 'react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8080';

function FileUpload({ token, onFileUploaded }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState('');

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

    setUploading(true);
    setMessage('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        },
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
