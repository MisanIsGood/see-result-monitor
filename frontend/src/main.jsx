import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import App from './App'
import './assets/global.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
      <Toaster
        position="top-center"
        toastOptions={{
          style: {
            background: '#111827',
            color: '#f0f4ff',
            border: '1px solid #1e2d4a',
            fontFamily: "'Sora', sans-serif",
            fontSize: '14px',
            borderRadius: '12px',
            padding: '12px 16px',
          },
          success: {
            iconTheme: { primary: '#10b981', secondary: '#111827' },
            duration: 4000,
          },
          error: {
            iconTheme: { primary: '#ef4444', secondary: '#111827' },
            duration: 5000,
          },
        }}
      />
    </BrowserRouter>
  </React.StrictMode>
)
