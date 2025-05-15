import React, { useState, useEffect } from 'react';
import './App.css';
import Login from './components/Login';
import Dashboard from './components/Dashboard';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [user, setUser] = useState(localStorage.getItem('user'));

  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('token');
    }
  }, [token]);

  const handleLogout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  };

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-left">
          <h1>Video to MP3 Converter</h1>
        </div>
        {token && (
          <button onClick={handleLogout} className="logout-btn">
            Logout
          </button>
        )}
      </header>
      <main>
        {!token ? (
          <Login setToken={setToken} setUser={setUser} />
        ) : (
          <Dashboard token={token} user={user} />
        )}
      </main>
    </div>
  );
}

export default App;
