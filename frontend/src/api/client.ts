import axios, { type InternalAxiosRequestConfig } from "axios";
import { message } from "antd";

// Allow callers (e.g. Step 5.4 U1 upload page) to suppress the global
// error toast when they want to surface a friendlier page-local message
// instead. Pass `{ suppressToast: true }` in the axios config.
declare module "axios" {
  interface AxiosRequestConfig {
    suppressToast?: boolean;
  }
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE ?? "http://localhost:8000",
  timeout: 30_000,
});

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const userId = sessionStorage.getItem("userId") ?? "";
  config.headers.set("X-User-Id", userId);
  return config;
});

api.interceptors.response.use(
  (response) => {
    const data = response.data;
    if (data && typeof data === "object" && "code" in data && data.code !== 0) {
      if (!response.config.suppressToast) {
        const msg = (data as { msg?: string }).msg ?? "unknown_error";
        message.error(msg);
      }
    }
    return response;
  },
  (error) => {
    if (!error.config?.suppressToast) {
      const data = error.response?.data;
      const msg =
        (data && typeof data === "object" && (data as { msg?: string }).msg) ||
        error.message ||
        "network_error";
      message.error(msg);
    }
    return Promise.reject(error);
  },
);

export default api;
