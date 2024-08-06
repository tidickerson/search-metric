import React, { useState } from 'react';
import axios from 'axios';

function Upload({ searchTerm, setMetrics }) {
  const [file, setFile] = useState(null);
  const [progress, setProgress] = useState({ started: false, pc: 0 });
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
        axios.post('http://127.0.0.1:5000/search?endpoint=https%3A%2F%2Ftidickerson2&version=2024-05-01-preview&service=tidickerson2&index=fever-index&result_file=output.json', jsonContent, {
          headers: {
            'Content-Type': 'application/json',
          },
          onUploadProgress: progressEvent => {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setProgress({ started: true, pc: percentCompleted });
          },
        })
        .then(res => {
          setMsg('Upload Successful');
          setMetrics(res.data);
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
    reader.readAsText(file);
  };

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  return (
    <div>
      <h1>Uploading Files in React</h1>
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUpload}>Upload</button>
      {progress.started && <p>Progress: {progress.pc}%</p>}
      {msg && <p>{msg}</p>}
    </div>
  );
}

export default Upload;
