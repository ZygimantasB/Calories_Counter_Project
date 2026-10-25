import axios from 'axios';

// Use empty string for production (same-origin), or localhost for dev server
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

// Helper function to get CSRF token from cookies
function getCsrfToken() {
  const name = 'csrftoken';
  const cookies = document.cookie.split(';');
  for (const cookie of cookies) {
    const [cookieName, cookieValue] = cookie.trim().split('=');
    if (cookieName === name) {
      return cookieValue;
    }
  }
  return null;
}

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Request interceptor for adding CSRF token to mutating requests
apiClient.interceptors.request.use(
  (config) => {
    // Add CSRF token for state-changing requests
    if (['post', 'put', 'patch', 'delete'].includes(config.method?.toLowerCase())) {
      const csrfToken = getCsrfToken();
      if (csrfToken) {
        config.headers['X-CSRFToken'] = csrfToken;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const { response, config } = error;
    
    console.group('%c[API Error Request Failure]', 'color: #f97316; font-weight: bold; font-size: 12px;');
    console.error(`Failed Route: ${config?.method?.toUpperCase()} ${config?.url}`);
    
    if (response) {
      console.error(`Status Code: ${response.status} (${response.statusText})`);
      console.error('Response Data:', response.data);
      if (response.status === 403) {
        console.warn('Hint: This might be a CSRF verification failure. Check the csrftoken cookie.');
      } else if (response.status === 401) {
        console.warn('Hint: Authentication is required for this endpoint.');
      }
    } else if (error.request) {
      console.error('No response received from server. This might be a CORS error, network disconnect, or backend server crash.');
    } else {
      console.error('Request setup error:', error.message);
    }
    
    console.groupEnd();
    return Promise.reject(error);
  }
);

export default apiClient;
