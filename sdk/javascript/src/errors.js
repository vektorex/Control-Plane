/**
 * Structured SDK Error Classes for AI Work Layer.
 * Preserves request_id, error code, and HTTP status code.
 */

export class APIError extends Error {
  constructor(message, statusCode, code = "api_error", requestId = null, details = null) {
    super(message);
    this.name = "APIError";
    this.statusCode = statusCode;
    this.code = code;
    this.requestId = requestId;
    this.details = details;
  }
}

export class AuthenticationError extends APIError {
  constructor(message, statusCode = 401, code = "authentication_failed", requestId = null) {
    super(message, statusCode, code, requestId);
    this.name = "AuthenticationError";
  }
}

export class AuthorizationError extends APIError {
  constructor(message, statusCode = 403, code = "permission_denied", requestId = null, details = null) {
    super(message, statusCode, code, requestId, details);
    this.name = "AuthorizationError";
  }
}

export class ValidationError extends APIError {
  constructor(message, statusCode = 400, code = "validation_error", requestId = null, details = null) {
    super(message, statusCode, code, requestId, details);
    this.name = "ValidationError";
  }
}

export class NotFoundError extends APIError {
  constructor(message, statusCode = 404, code = "not_found", requestId = null, details = null) {
    super(message, statusCode, code, requestId, details);
    this.name = "NotFoundError";
  }
}

export class ConflictError extends APIError {
  constructor(message, statusCode = 409, code = "conflict", requestId = null, details = null) {
    super(message, statusCode, code, requestId, details);
    this.name = "ConflictError";
  }
}

export class RateLimitError extends APIError {
  constructor(message, statusCode = 429, code = "rate_limit_exceeded", requestId = null, retryAfter = 60) {
    super(message, statusCode, code, requestId);
    this.name = "RateLimitError";
    this.retryAfter = retryAfter;
  }
}

export class PolicyError extends APIError {
  constructor(message, statusCode = 403, code = "policy_error", requestId = null) {
    super(message, statusCode, code, requestId);
    this.name = "PolicyError";
  }
}

export class GovernanceError extends APIError {
  constructor(message, statusCode = 403, code = "governance_denied", requestId = null, details = null) {
    super(message, statusCode, code, requestId, details);
    this.name = "GovernanceError";
  }
}

export class ExecutionError extends APIError {
  constructor(message, statusCode = 500, code = "execution_error", requestId = null) {
    super(message, statusCode, code, requestId);
    this.name = "ExecutionError";
  }
}

export class DependencyError extends APIError {
  constructor(message, statusCode = 502, code = "dependency_error", requestId = null) {
    super(message, statusCode, code, requestId);
    this.name = "DependencyError";
  }
}

export function parseErrorFromResponse(status, data, headers = {}) {
  const err = data?.error || {};
  const message = err.message || `Request failed with status ${status}`;
  const code = err.code || "unknown_error";
  const reqId = err.request_id || headers["x-request-id"] || null;
  const details = err.details || null;

  switch (status) {
    case 401:
      return new AuthenticationError(message, status, code, reqId);
    case 403:
      if (err.type === "governance_error") {
        return new GovernanceError(message, status, code, reqId, details);
      }
      return new AuthorizationError(message, status, code, reqId, details);
    case 400:
    case 422:
      return new ValidationError(message, status, code, reqId, details);
    case 404:
      return new NotFoundError(message, status, code, reqId, details);
    case 409:
      return new ConflictError(message, status, code, reqId, details);
    case 429: {
      const retryAfter = parseInt(headers["retry-after"] || "60", 10);
      return new RateLimitError(message, status, code, reqId, retryAfter);
    }
    case 502:
    case 503:
    case 504:
      return new DependencyError(message, status, code, reqId);
    default:
      return new APIError(message, status, code, reqId, details);
  }
}
