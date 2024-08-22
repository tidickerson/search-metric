import React, { useState } from 'react';
import axios from 'axios';

function UploadLabels() {
  const [file, setFile] = useState(null);
  const [msg, setMsg] = useState(null);

  const handleUpload = () => {
    if (!file) {
      setMsg('No file selected');
      return;
    }
  
    const reader = new FileReader();
  
    reader.onload = function (e) {
      try {
        // Parse the JSON content from the file
        const jsonContent = JSON.parse(e.target.result);
  
        // Upload the modified JSON content
        axios.post('http://127.0.0.1:5000/upload_truth', jsonContent, {
          headers: {
            'Content-Type': 'application/json',
          },
        })
        .then(res => {
          setMsg('Upload Successful');
        })
        .catch(error => {
          setMsg('Upload Failed');
          console.error('Error message:', error.message);
          if (error.response) {
            console.error('Response data:', error.response.data);
            console.error('Status code:', error.response.status);
            console.error('Headers:', error.response.headers);
          } else if (error.request) {
            console.error('Request data:', error.request);
          } else {
            console.error('Error:', error.message);
          }
        });
      } catch (err) {
        setMsg('Invalid JSON file');
        console.error('Error parsing JSON:', err);
      }
    };
  
    reader.onerror = function (err) {
      setMsg('Error reading file');
      console.error('FileReader error:', err);
    };
  
    reader.readAsText(file);
  };

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  return (
    <div>
      <h1>Upload Ground Truth Labels</h1>
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUpload}>Upload Ground Truth</button>
      {msg && <p>{msg}</p>}
    </div>
  );
}

export default UploadLabels;
