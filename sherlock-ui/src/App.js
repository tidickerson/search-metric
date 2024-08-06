import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Results from './components/Results';
import Upload from './components/Upload';
import UploadLabels from './components/UploadLabels';
import './App.css';

function App() {
  const [metrics, setMetrics] = useState(null);

  

  return (
    <div className="App">
      <div className="container">
        <Sidebar />
        <main>
          <header>
            <UploadLabels/>
            <Upload setMetrics={setMetrics} />
          </header>
          <Results metrics={metrics} />
        </main>
      </div>
    </div>
  );
}

export default App;
