import React, { useState, useEffect, useCallback } from 'react';
import FileUpload from './FileUpload';
import FileList from './FileList';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8080';

function Dashboard({ token, user }) {
  const [uploadedFiles, setUploadedFiles] = useState([]);

  const handleFileUploaded = (fileInfo) => {
    setUploadedFiles(prev => [...prev, fileInfo]);
  };

  const handleFileDeleted = (videoKey) => {
    setUploadedFiles(prev => prev.filter(file => file.videoKey !== videoKey));
  };

  // Check conversion status for processing files
  const checkFileStatus = useCallback(async (file) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/check-audio/${file.videoKey}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      return {
        status: response.data.status,
        audioKey: response.data.audio_key || file.audioKey
      };
    } catch (err) {
      console.error('Status check error:', err);
      return { status: 'processing' };
    }
  }, [token]);

  // Poll for file status updates
  useEffect(() => {
    const pollInterval = setInterval(async () => {
      const updatedFiles = await Promise.all(
        uploadedFiles.map(async (file) => {
          if (file.status === 'processing') {
            const statusUpdate = await checkFileStatus(file);
            return { ...file, ...statusUpdate };
          }
          return file;
        })
      );
      
      // Only update if there are actual changes
      const hasChanges = updatedFiles.some((file, index) => 
        file.status !== uploadedFiles[index]?.status
      );
      
      if (hasChanges) {
        setUploadedFiles(updatedFiles);
      }
    }, 5000); // Check every 5 seconds

    return () => clearInterval(pollInterval);
  }, [uploadedFiles, checkFileStatus]);

  return (
    <div className="dashboard">
      <h2>Welcome, {user}!</h2>
      <div className="dashboard-content">
        <FileUpload token={token} onFileUploaded={handleFileUploaded} />
        <FileList 
          token={token} 
          files={uploadedFiles} 
          onFileDeleted={handleFileDeleted}
        />
      </div>
    </div>
  );
}

export default Dashboard;
