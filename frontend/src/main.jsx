import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.jsx';
// Bootstrap first so our own rules can override it. The old single-file
// version pulled this from a CDN, which is why the layout broke when the
// app was split up: the components still use btn/table/d-flex classes.
import 'bootstrap/dist/css/bootstrap.min.css';
import './styles.css';

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
