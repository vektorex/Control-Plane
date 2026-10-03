import { env } from "@/config/env";
import { supabase } from "./supabaseClient";

export class ApiError extends Error {
  constructor(message, status = 500, details = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

/**
 * Base HTTP client configured to talk to the backend service with Supabase Auth token injection.
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

  // Retrieve current active Supabase Auth token if not provided explicitly
  let authHeader = headers["Authorization"] || headers["authorization"];
  if (!authHeader && supabase?.auth) {
    try {
      const { data } = await supabase.auth.getSession();
      if (data?.session?.access_token) {
        authHeader = `Bearer ${data.session.access_token}`;
      }
    } catch {}
  }

  const isFormData = typeof FormData !== "undefined" && body instanceof FormData;

  // Tenant context injection from localStorage if available in browser
  let orgHeader = headers["X-Organization-Id"] || headers["x-organization-id"];
  let wsHeader = headers["X-Workspace-Id"] || headers["x-workspace-id"];
  if (typeof window !== "undefined") {
    if (!orgHeader) {
      const storedOrg = localStorage.getItem("ai_layer_active_org_id");
      if (storedOrg) orgHeader = storedOrg;
    }
    if (!wsHeader) {
      const storedWs = localStorage.getItem("ai_layer_active_workspace_id");
      if (storedWs) wsHeader = storedWs;
    }
  }

  const defaultHeaders = {
    ...(isFormData ? {} : { "Content-Type": "application/json" }),
    Accept: "application/json",
    ...(authHeader ? { Authorization: authHeader } : {}),
    ...(orgHeader ? { "X-Organization-Id": orgHeader } : {}),
    ...(wsHeader ? { "X-Workspace-Id": wsHeader } : {}),
    ...headers,
  };

  try {
    const response = await fetch(url, {
      method,
      headers: defaultHeaders,
      body: isFormData ? body : body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });

    clearTimeout(id);

    const isJson = response.headers.get("content-type")?.includes("application/json");
    const data = isJson ? await response.json() : await response.text();

    if (!response.ok) {
      const errorMsg =
        data?.error?.message ||
        data?.detail ||
        data?.message ||
        `HTTP Error ${response.status}: ${response.statusText}`;

      // Handle 401 Unauthorized redirect in browser
      if (response.status === 401 && typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
        // Optional: window.location.href = "/login";
      }

      throw new ApiError(errorMsg, response.status, data);
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
