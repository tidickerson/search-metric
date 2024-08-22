import React, { useState } from 'react';
import axios from 'axios';
import configData from '../azs_config.json';

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
        // Upload the modified JSON content
        const endpoint = encodeURIComponent(configData.endpoint);
        const apiVersion = configData.api_version;
        const serviceName = configData.service_name;
        const indexName = configData.index_name;
        const resultFile = configData.result_file;

        

        axios.post(`http://127.0.0.1:5000/search?endpoint=${endpoint}&version=${apiVersion}&service=${serviceName}&index=${indexName}&result_file=${resultFile}`, jsonContent, {
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
      <h1>Upload Search Template</h1>
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUpload}>Calculate Metrics</button>
      {progress.started && <p>Progress: {progress.pc}%</p>}
      {msg && <p>{msg}</p>}
    </div>
  );
}

export default Upload;
