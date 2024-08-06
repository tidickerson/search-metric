import React from 'react';
import './Params.css';

function Params() {
  return (
    <div className="params">
      <select>
        <option>Embedding Model</option>
        <option>Open AI ...</option>
        <option>Cohere ...</option>
      </select>
      <select>
        <option>Dimensions</option>
        <option>512</option>
        <option>1024</option>
      </select>
      <select>
        <option>Search Mode</option>
        <option>Text Search</option>
        <option>Vector Search</option>
      </select>
      <select>
        <option>Semantic</option>
        <option>Enabled</option>
        <option>Disabled</option>
      </select>
      <select>
        <option>Oversampling</option>
      </select>
      <select>
        <option>Query Type...</option>
      </select>
    </div>
  );
}

export default Params;
