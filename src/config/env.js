/**
 * Environment configuration helper with validation and safe defaults.
 * Prevents hardcoding secrets and provides a single source of truth for runtime variables.
 */
export const env = {
  isProduction: process.env.NODE_ENV === "production",
  isDevelopment: process.env.NODE_ENV === "development",
  isTest: process.env.NODE_ENV === "test",

  app: {
    name: process.env.NEXT_PUBLIC_APP_NAME || "AI Work Layer",
    url: process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000",
    defaultWorkspace: process.env.NEXT_PUBLIC_DEFAULT_WORKSPACE_NAME || "Default Workspace",
  },

  orchestrator: {
    // URL pointing to the future Python/FastAPI orchestration backend
    apiUrl: process.env.NEXT_PUBLIC_ORCHESTRATION_API_URL || "http://localhost:8000/api/v1",
    apiSecret: process.env.ORCHESTRATION_API_SECRET || "",
    timeoutMs: 30000,
  },

  features: {
    enableDebugLogs: process.env.NEXT_PUBLIC_ENABLE_DEBUG_LOGS === "true",
  },
};

/**
 * Validates critical environment settings at startup or runtime.
 * Logs structured warnings if required backend variables are missing.
 */
export function validateEnv() {
  const missing = [];

  if (env.isProduction && !process.env.NEXT_PUBLIC_APP_URL) {
    missing.push("NEXT_PUBLIC_APP_URL");
  }

  if (missing.length > 0 && env.features.enableDebugLogs) {
    console.warn(`[Config] Optional env variables not set: ${missing.join(", ")}`);
  }

  return {
    valid: missing.length === 0,
    missing,
  };
}
