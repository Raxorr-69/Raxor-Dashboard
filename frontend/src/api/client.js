import { API_BASE_URL } from "../lib/constants";
import { clearToken, getToken } from "../lib/storage";

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request(path, { method = "GET", body, params } = {}) {
  const url = new URL(`${API_BASE_URL}${path}`);

  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, value);
      }
    }
  }

  const token = getToken();

  const headers = { "Content-Type": "application/json" };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(url.toString(), {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (response.status === 401) {
    clearToken();
    window.location.href = "/login";
    throw new ApiError("Your session expired. Please log in again.", 401);
  }

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const data = await response.json();
      detail = data.detail || detail;
    } catch {
      // Response body wasn't JSON — fall back to statusText.
    }
    throw new ApiError(detail, response.status);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export const apiClient = {
  get: (path, params) => request(path, { method: "GET", params }),
  post: (path, body, params) => request(path, { method: "POST", body, params }),
  patch: (path, body, params) => request(path, { method: "PATCH", body, params }),
  put: (path, body, params) => request(path, { method: "PUT", body, params }),
  delete: (path, params) => request(path, { method: "DELETE", params }),
};
