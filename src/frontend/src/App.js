import React, { useState, useEffect } from 'react';
import './App.css';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import { jwtDecode } from 'jwt-decode';

function App() {
  const [authenticated, setAuthenticated] = useState(false);
  const [token, setToken] = useState('');
  const [user, setUser] = useState('');
  const [userData, setUserData] = useState(null);

  // On component mount, check if token exists and is valid
  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    if (storedToken) {
      try {
        // Validate token by decoding it
        const decoded = jwtDecode(storedToken);
        
        // Check if token is expired
        const currentTime = Date.now() / 1000;
        if (decoded.exp && decoded.exp < currentTime) {
          // Token is expired, clear localStorage
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          localStorage.removeItem('authenticated');
          console.log('Token expired');
        } else {
          // Token is valid
          setToken(storedToken);
          setUser(decoded.username || localStorage.getItem('user'));
          setUserData(decoded); // Store all user data from token
          setAuthenticated(decoded.authenticated === true);
        }
      } catch (error) {
        // Invalid token
        console.error('Invalid token:', error);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        localStorage.removeItem('authenticated');
      }
    }
  }, []);

  useEffect(() => {
    if (authenticated) {
      localStorage.setItem('authenticated', 'true');
      if (token) {
        localStorage.setItem('token', token);
      }
      if (user) {
        localStorage.setItem('user', user);
      }
    } else {
      localStorage.removeItem('authenticated');
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    }
  }, [authenticated, token, user]);

  const handleLogout = () => {
    setAuthenticated(false);
    setToken('');
    setUser('');
    setUserData(null);
  };

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-left">
          <h1>Video to MP3 Converter</h1>
        </div>
        {authenticated && (
          <button onClick={handleLogout} className="logout-btn">
            Logout
          </button>
        )}
      </header>
      <main>
        {!authenticated ? (
          <Login setAuthenticated={setAuthenticated} setUser={setUser} setToken={setToken} setUserData={setUserData} />
        ) : (
          <Dashboard user={user} token={token} userData={userData} />
        )}
      </main>
    </div>
  );
}

export default App;
