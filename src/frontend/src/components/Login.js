import React, { useState } from 'react';
import axios from 'axios';
import { jwtDecode } from 'jwt-decode';

const AUTH_API_URL = 'http://localhost:5000';

function Login({ setAuthenticated, setUser, setToken, setUserData }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      console.log('Attempting login with:', email);
      // Use Basic Authentication with your auth service
      const credentials = btoa(`${email}:${password}`);
      console.log('Encoded credentials:', credentials);
      
      console.log('Sending login request to:', `${AUTH_API_URL}/login`);
      const response = await axios.post(`${AUTH_API_URL}/login`, {}, {
        headers: {
          'Authorization': `Basic ${credentials}`,
        },
      });

      console.log('Login response:', response);
      // Get the token from the response, handling different possible formats
      let token;
      if (typeof response.data === 'string') {
        token = response.data;
      } else if (typeof response.data === 'object' && response.data.token) {
        token = response.data.token;
      } else {
        console.error('Unexpected token format:', response.data);
        setError('Unexpected response from server');
        setLoading(false);
        return;
      }
      
      console.log('Extracted token:', token);
      
      try {
        // Decode the token to get user information
        console.log('Attempting to decode token');
        const decoded = jwtDecode(token);
        console.log('Decoded token:', decoded);
        
        // Store token and user info
        localStorage.setItem('token', token);
        localStorage.setItem('user', decoded.username || email);
        
        setToken(token);
        setUser(decoded.username || email);
        setUserData(decoded);
        setAuthenticated(true);
      } catch (decodeError) {
        console.error('Error decoding token:', decodeError);
        console.log('Token that failed to decode:', token);
        setError('Authentication error. Could not decode token.');
      }
    } catch (err) {
      console.error('Login error:', err);
      if (err.response) {
        console.error('Error response data:', err.response.data);
        console.error('Error response status:', err.response.status);
        console.error('Error response headers:', err.response.headers);
      } else if (err.request) {
        console.error('No response received:', err.request);
      } else {
        console.error('Error setting up request:', err.message);
      }
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
          <label htmlFor="email">Email:</label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
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
