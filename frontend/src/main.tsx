import './lib/i18n/i18n';
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';

import { App } from './app/App';
import { AuthProvider } from './features/auth/AuthContext';
import './styles/index.css';

document.documentElement.dir = 'rtl';
document.documentElement.lang = 'he';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);
