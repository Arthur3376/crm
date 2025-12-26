import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";

// Suppress ResizeObserver loop error (benign browser warning)
// This error is caused by browser's ResizeObserver and doesn't affect functionality
if (typeof window !== 'undefined') {
  const errorHandler = (e) => {
    if (e.message && e.message.includes('ResizeObserver loop')) {
      const resizeObserverErrDiv = document.getElementById('webpack-dev-server-client-overlay-div');
      const resizeObserverErr = document.getElementById('webpack-dev-server-client-overlay');
      if (resizeObserverErrDiv) {
        resizeObserverErrDiv.style.display = 'none';
      }
      if (resizeObserverErr) {
        resizeObserverErr.style.display = 'none';
      }
      e.stopImmediatePropagation();
      e.preventDefault();
      return true;
    }
  };
  
  window.addEventListener('error', errorHandler, true);
  window.addEventListener('unhandledrejection', (e) => {
    if (e.reason && e.reason.message && e.reason.message.includes('ResizeObserver')) {
      e.preventDefault();
    }
  });
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
