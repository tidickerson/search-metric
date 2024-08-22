import React from 'react';
import './Sidebar.css';
import azure_logo from '../assets/azure_logo.png'; 

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="logo">
      <img src={azure_logo} alt="Azure Logo" className="logo-image" />
      </div>
    </aside>
  );
}

export default Sidebar;
