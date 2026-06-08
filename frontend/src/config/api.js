/**
 * Centralized API Configuration
 * All backend URLs are configured here and use environment variables
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const API_CONFIG = {
  // Base URL
  baseURL: API_BASE_URL,

  // Auth endpoints
  auth: {
    login: `${API_BASE_URL}/api/auth/login`,
    register: `${API_BASE_URL}/api/auth/register`,
    profile: `${API_BASE_URL}/api/auth/profile`,
    admin_profile: `${API_BASE_URL}/api/auth/admin/profile`,
  },

  // Search endpoints
  search: {
    chunks: `${API_BASE_URL}/api/search`,
    generate: `${API_BASE_URL}/api/generate`,
  },

  // Document endpoints
  documents: {
    list: `${API_BASE_URL}/api/documents`,
    ingest: `${API_BASE_URL}/api/ingest`,
    getChunks: (docId) => `${API_BASE_URL}/api/documents/${docId}/chunks`,
  },

  // Metrics & Admin endpoints
  metrics: {
    main: `${API_BASE_URL}/api/metrics`,
    health: `${API_BASE_URL}/api/health/detailed`,
  },

  // Feedback endpoints
  feedback: {
    submit: `${API_BASE_URL}/api/feedback`,
    analytics: `${API_BASE_URL}/api/admin/feedback-analytics`,
    lowConfidence: `${API_BASE_URL}/api/admin/low-confidence-queries`,
  },

  // Cache endpoints
  cache: {
    stats: `${API_BASE_URL}/api/cache/stats`,
    queryPerformance: `${API_BASE_URL}/api/cache/query-performance`,
    clear: `${API_BASE_URL}/api/cache/clear`,
  },

  // Monitoring endpoints
  monitoring: {
    metrics: `${API_BASE_URL}/api/monitoring/metrics`,
    alerts: `${API_BASE_URL}/api/alerts/status`,
  },

  // User endpoints
  user: {
    stats: `${API_BASE_URL}/api/user/stats`,
  },

  // Admin endpoints
  admin: {
    users: `${API_BASE_URL}/api/auth/admin/users`,
  },
};

/**
 * Helper function to get API URL
 * @param {string} path - API path (e.g., '/api/search')
 * @returns {string} Full API URL
 */
export const getAPIURL = (path) => {
  return `${API_BASE_URL}${path}`;
};

export default API_CONFIG;
