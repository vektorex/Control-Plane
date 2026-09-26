import { env } from "@/config/env";

export class ApiError extends Error {
  constructor(message, status = 500, details = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

/**
 * Base HTTP client configured to talk to the backend service.
 * Ready for connection to the Python/FastAPI orchestration backend.
 */
export async function apiClient(endpoint, options = {}) {
  const {
    method = "GET",
    headers = {},
    body,
    params,
    timeout = env.orchestrator.timeoutMs,
  } = options;

  let url = endpoint.startsWith("http")
    ? endpoint
    : `${env.orchestrator.apiUrl}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value));
      }
    });
    const queryString = searchParams.toString();
    if (queryString) {
      url += (url.includes("?") ? "&" : "?") + queryString;
    }
  }

  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);

  const defaultHeaders = {
    "Content-Type": "application/json",
    Accept: "application/json",
    ...(env.orchestrator.apiSecret
      ? { Authorization: `Bearer ${env.orchestrator.apiSecret}` }
      : {}),
    ...headers,
  };

  try {
    const response = await fetch(url, {
      method,
      headers: defaultHeaders,
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });

    clearTimeout(id);

    const isJson = response.headers.get("content-type")?.includes("application/json");
    const data = isJson ? await response.json() : await response.text();

    if (!response.ok) {
      throw new ApiError(
        data?.detail || data?.message || `HTTP Error ${response.status}: ${response.statusText}`,
        response.status,
        data
      );
    }

    return data;
  } catch (error) {
    clearTimeout(id);
    if (error.name === "AbortError") {
      throw new ApiError(`Request timed out after ${timeout}ms`, 408);
    }
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(error.message || "Network error communicating with orchestration service", 503);
  }
}
