import React, { useState } from 'react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8080';

function Login({ setToken, setUser }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const credentials = btoa(`${username}:${password}`);
      console.log('Credentials:', credentials); // Debug
      console.log('Username:', username); // Debug
      
      const response = await axios.post(`${API_BASE_URL}/login`, {}, {
        headers: {
          'Authorization': `Basic ${credentials}`,
        },
      });

      console.log('Login response:', response); // Debug
      const token = response.data;
      setToken(token);
      setUser(username);
      localStorage.setItem('token', token);
      localStorage.setItem('user', username);
    } catch (err) {
      console.error('Full login error:', err); // More detailed error
      console.error('Error response:', err.response); // Response details
      setError('Invalid credentials. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <h2>Login</h2>
      <form onSubmit={handleSubmit} className="login-form">
        <div className="form-group">
          <label htmlFor="username">Email:</label>
          <input
            type="email"
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="password">Password:</label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        {error && <div className="error">{error}</div>}
        <button type="submit" disabled={loading}>
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </form>
    </div>
  );
}

export default Login;
