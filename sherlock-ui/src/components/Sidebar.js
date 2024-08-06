import React from 'react';
import './Sidebar.css';

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="logo">
        <nav>
          <ul>
            <li>
              <a href="#">Parameters</a>
            </li>
            <li>
              <a href="#">Search History</a>
            </li>
            <li>
              <a href="#">Create Index</a>
            </li>
            <li>
              <a href="#">Index Documents</a>
            </li>
          </ul>
        </nav>
      </div>
    </aside>
  );
}

export default Sidebar;
