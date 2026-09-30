import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.jsx';
// Bootstrap first so our own rules override it; components rely on btn/table/d-flex.
import 'bootstrap/dist/css/bootstrap.min.css';
import './styles.css';

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
