import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000,
});

// Request Interceptor: Attach JWT Bearer Token safely
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("areca_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      // Safe masked logging for debugging (never log raw tokens)
      if (import.meta.env.DEV) {
        const masked = `${token.substring(0, 6)}...${token.substring(token.length - 4)}`;
        // config.headers['X-Auth-Debug'] = masked;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Extract data & handle 401 Unauthorized
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response) {
      if (error.response.status === 401) {
        localStorage.removeItem("areca_token");
        localStorage.removeItem("areca_user");
        if (window.location.pathname !== "/login" && window.location.pathname !== "/register") {
          window.location.href = "/login";
        }
      }
      const message =
        error.response.data?.detail ||
        error.response.data?.message ||
        `Request failed with status ${error.response.status}`;
      return Promise.reject(new Error(message));
    } else if (error.request) {
      return Promise.reject(new Error("Unable to reach ArecaAgent backend server. Please check connection."));
    }
    return Promise.reject(error);
  }
);

export default apiClient;
