/**
 * Core AIWorkLayer API Client for JavaScript.
 * Automatically attaches authentication, handles bounded retries for idempotent/read requests,
 * and parses structured domain errors.
 */

import { parseErrorFromResponse } from "./errors.js";

export class AIWorkLayerClient {
  constructor(options = {}) {
    this.apiKey = options.apiKey || (typeof process !== "undefined" ? process.env.AWL_API_KEY : null);
    this.baseUrl = (options.baseUrl || "http://localhost:8000/api/v1").replace(/\/$/, "");
    this.maxRetries = options.maxRetries !== undefined ? options.maxRetries : 2;
    this.timeoutMs = options.timeoutMs || 30000;

    if (!this.apiKey) {
      throw new Error("AIWorkLayerClient requires an apiKey.");
    }

    // Initialize resource sub-clients
    this.tasks = new TasksResource(this);
    this.runs = new RunsResource(this);
    this.workflows = new WorkflowsResource(this);
    this.artifacts = new ArtifactsResource(this);
    this.documents = new DocumentsResource(this);
    this.models = new ModelsResource(this);
    this.connectors = new ConnectorsResource(this);
    this.memory = new MemoryResource(this);
    this.knowledge = new KnowledgeResource(this);
    this.usage = new UsageResource(this);
    this.webhooks = new WebhooksResource(this);
    this.marketplace = new MarketplaceResource(this);
    this.collaboration = new CollaborationResource(this);
  }


  async request(method, path, options = {}) {
    const url = `${this.baseUrl}${path.startsWith("/") ? path : `/${path}`}`;
    const headers = {
      "Authorization": `Bearer ${this.apiKey}`,
      "Accept": "application/json",
      ...(options.headers || {}),
    };

    if (options.body && typeof options.body === "object" && !(options.body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
    }

    if (options.idempotencyKey) {
      headers["Idempotency-Key"] = options.idempotencyKey;
    }

    const isGet = method.toUpperCase() === "GET";
    const allowRetry = isGet || Boolean(options.idempotencyKey);
    let attempts = 0;
    let lastError = null;

    while (attempts <= (allowRetry ? this.maxRetries : 0)) {
      attempts++;
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeoutMs);

        const fetchOptions = {
          method,
          headers,
          signal: controller.signal,
          body: options.body ? (typeof options.body === "string" ? options.body : JSON.stringify(options.body)) : undefined,
        };

        const response = await fetch(url, fetchOptions);
        clearTimeout(timeoutId);

        const responseHeaders = {};
        response.headers.forEach((val, key) => {
          responseHeaders[key.toLowerCase()] = val;
        });

        if (response.status === 204) {
          return null;
        }

        let responseData = null;
        const contentType = response.headers.get("content-type") || "";
        if (contentType.includes("application/json")) {
          responseData = await response.json();
        } else {
          responseData = await response.text();
        }

        if (!response.ok) {
          const parsedErr = parseErrorFromResponse(response.status, responseData, responseHeaders);
          // If server error and retries allowed, retry
          if (response.status >= 500 && allowRetry && attempts <= this.maxRetries) {
            await new Promise((resolve) => setTimeout(resolve, attempts * 500));
            continue;
          }
          throw parsedErr;
        }

        return responseData;
      } catch (err) {
        lastError = err;
        if (!allowRetry || attempts > this.maxRetries || err.name === "AbortError") {
          throw err;
        }
        await new Promise((resolve) => setTimeout(resolve, attempts * 500));
      }
    }
    throw lastError;
  }
}

class TasksResource {
  constructor(client) {
    this.client = client;
  }

  async run(taskId, payload = {}, options = {}) {
    return this.client.request("POST", `/tasks/${taskId}/runs`, {
      body: payload,
      idempotencyKey: options.idempotencyKey,
    });
  }
}

class RunsResource {
  constructor(client) {
    this.client = client;
  }

  async get(runId) {
    return this.client.request("GET", `/runs/${runId}`);
  }

  async result(runId) {
    return this.client.request("GET", `/runs/${runId}/result`);
  }

  async events(runId) {
    return this.client.request("GET", `/runs/${runId}/events`);
  }

  async usage(runId) {
    return this.client.request("GET", `/runs/${runId}/usage`);
  }

  async evaluation(runId) {
    return this.client.request("GET", `/runs/${runId}/evaluation`);
  }

  stream(runId) {
    const url = `${this.client.baseUrl}/runs/${runId}/stream`;
    return url;
  }
}

class WorkflowsResource {
  constructor(client) {
    this.client = client;
  }

  async list() {
    return this.client.request("GET", "/workflows");
  }

  async get(workflowId) {
    return this.client.request("GET", `/workflows/${workflowId}`);
  }

  async run(workflowId, payload = {}, options = {}) {
    return this.client.request("POST", `/workflows/${workflowId}/runs`, {
      body: payload,
      idempotencyKey: options.idempotencyKey,
    });
  }

  async runStatus(runId) {
    return this.client.request("GET", `/workflows/runs/${runId}`);
  }
}

class ArtifactsResource {
  constructor(client) {
    this.client = client;
  }

  async create(data) {
    return this.client.request("POST", "/artifacts", { body: data });
  }

  async get(artifactId) {
    return this.client.request("GET", `/artifacts/${artifactId}`);
  }

  async parts(artifactId) {
    return this.client.request("GET", `/artifacts/${artifactId}/parts`);
  }
}

class DocumentsResource {
  constructor(client) {
    this.client = client;
  }

  async list() {
    return this.client.request("GET", "/documents");
  }

  async get(documentId) {
    return this.client.request("GET", `/documents/${documentId}`);
  }
}

class ModelsResource {
  constructor(client) {
    this.client = client;
  }

  async list() {
    return this.client.request("GET", "/models");
  }
}

class ConnectorsResource {
  constructor(client) {
    this.client = client;
  }

  async list() {
    return this.client.request("GET", "/connectors");
  }
}

class MemoryResource {
  constructor(client) {
    this.client = client;
  }

  async list() {
    return this.client.request("GET", "/memory");
  }

  async create(data) {
    return this.client.request("POST", "/memory", { body: data });
  }
}

class KnowledgeResource {
  constructor(client) {
    this.client = client;
  }

  async entities() {
    return this.client.request("GET", "/knowledge/entities");
  }

  async entity(entityId) {
    return this.client.request("GET", `/knowledge/entities/${entityId}`);
  }

  async relationships(entityId) {
    return this.client.request("GET", `/knowledge/entities/${entityId}/relationships`);
  }
}

class UsageResource {
  constructor(client) {
    this.client = client;
  }

  async get(params = {}) {
    const query = new URLSearchParams();
    if (params.periodHours) query.set("period_hours", params.periodHours);
    if (params.endpoint) query.set("endpoint", params.endpoint);
    const qs = query.toString();
    return this.client.request("GET", `/usage${qs ? `?${qs}` : ""}`);
  }
}

class WebhooksResource {
  constructor(client) {
    this.client = client;
  }

  async list() {
    return this.client.request("GET", "/webhooks");
  }

  async create(data) {
    return this.client.request("POST", "/webhooks", { body: data });
  }

  async get(subscriptionId) {
    return this.client.request("GET", `/webhooks/${subscriptionId}`);
  }

  async delete(subscriptionId) {
    return this.client.request("DELETE", `/webhooks/${subscriptionId}`);
  }
}

class MarketplaceResource {
  constructor(client) {
    this.client = client;
  }

  async list(params = {}) {
    const query = new URLSearchParams();
    if (params.query) query.set("query", params.query);
    if (params.category) query.set("category", params.category);
    if (params.packageType) query.set("package_type", params.packageType);
    if (params.visibility) query.set("visibility", params.visibility);
    if (params.status) query.set("status", params.status);
    if (params.limit) query.set("limit", params.limit);
    if (params.offset) query.set("offset", params.offset);
    const qs = query.toString();
    return this.client.request("GET", `/marketplace/packages${qs ? `?${qs}` : ""}`);
  }

  async get(slug) {
    return this.client.request("GET", `/marketplace/packages/${slug}`);
  }

  async versions(slug) {
    return this.client.request("GET", `/marketplace/packages/${slug}/versions`);
  }

  async install(packageId, data = {}, options = {}) {
    return this.client.request("POST", `/marketplace/packages/${packageId}/installations`, {
      body: data,
      idempotencyKey: options.idempotencyKey,
    });
  }

  async listInstallations(params = {}) {
    const query = new URLSearchParams();
    if (params.workspaceId) query.set("workspace_id", params.workspaceId);
    if (params.status) query.set("status", params.status);
    const qs = query.toString();
    return this.client.request("GET", `/marketplace/installations${qs ? `?${qs}` : ""}`);
  }

  async getInstallation(installationId) {
    return this.client.request("GET", `/marketplace/installations/${installationId}`);
  }

  async update(installationId, data = {}, options = {}) {
    return this.client.request("POST", `/marketplace/installations/${installationId}/update`, {
      body: data,
      idempotencyKey: options.idempotencyKey,
    });
  }

  async rollback(installationId, data = {}, options = {}) {
    return this.client.request("POST", `/marketplace/installations/${installationId}/rollback`, {
      body: data,
      idempotencyKey: options.idempotencyKey,
    });
  }

  async fork(packageId, data = {}, options = {}) {
    return this.client.request("POST", `/marketplace/packages/${packageId}/fork`, {
      body: data,
      idempotencyKey: options.idempotencyKey,
    });
  }

  async usage(packageId) {
    return this.client.request("GET", `/marketplace/packages/${packageId}/usage`);
  }
}

export class CollaborationCommentsResource {
  constructor(client) {
    this.client = client;
  }

  async list(sessionId, params = {}) {
    const query = new URLSearchParams();
    if (params.resourceType) query.set("resource_type", params.resourceType);
    if (params.resourceId) query.set("resource_id", params.resourceId);
    if (params.limit) query.set("limit", params.limit);
    if (params.offset) query.set("offset", params.offset);
    const qs = query.toString();
    return this.client.request("GET", `/collaboration/sessions/${sessionId}/comments${qs ? `?${qs}` : ""}`);
  }

  async create(sessionId, data, options = {}) {
    return this.client.request("POST", `/collaboration/sessions/${sessionId}/comments`, {
      body: data,
      idempotencyKey: options.idempotencyKey,
    });
  }
}

export class CollaborationAssignmentsResource {
  constructor(client) {
    this.client = client;
  }

  async list(sessionId, params = {}) {
    const query = new URLSearchParams();
    if (params.status) query.set("status", params.status);
    if (params.assignedTo) query.set("assigned_to", params.assignedTo);
    if (params.limit) query.set("limit", params.limit);
    if (params.offset) query.set("offset", params.offset);
    const qs = query.toString();
    return this.client.request("GET", `/collaboration/sessions/${sessionId}/assignments${qs ? `?${qs}` : ""}`);
  }

  async create(sessionId, data, options = {}) {
    return this.client.request("POST", `/collaboration/sessions/${sessionId}/assignments`, {
      body: data,
      idempotencyKey: options.idempotencyKey,
    });
  }
}

export class CollaborationSessionsResource {
  constructor(client) {
    this.client = client;
    this.comments = new CollaborationCommentsResource(client);
    this.assignments = new CollaborationAssignmentsResource(client);
  }

  async create(data, options = {}) {
    return this.client.request("POST", "/collaboration/sessions", {
      body: data,
      idempotencyKey: options.idempotencyKey,
    });
  }

  async list(params = {}) {
    const query = new URLSearchParams();
    if (params.workspaceId) query.set("workspace_id", params.workspaceId);
    if (params.resourceType) query.set("resource_type", params.resourceType);
    if (params.resourceId) query.set("resource_id", params.resourceId);
    if (params.status) query.set("status", params.status);
    if (params.limit) query.set("limit", params.limit);
    if (params.offset) query.set("offset", params.offset);
    const qs = query.toString();
    return this.client.request("GET", `/collaboration/sessions${qs ? `?${qs}` : ""}`);
  }

  async get(sessionId) {
    return this.client.request("GET", `/collaboration/sessions/${sessionId}`);
  }

  async events(sessionId, onEvent) {
    const url = `${this.client.baseUrl}/collaboration/sessions/${sessionId}/events`;
    if (typeof EventSource !== "undefined") {
      const es = new EventSource(url);
      if (onEvent) {
        es.onmessage = (e) => {
          try {
            onEvent(JSON.parse(e.data));
          } catch {
            onEvent(e.data);
          }
        };
      }
      return es;
    }
    return { url };
  }
}

export class CollaborationResource {
  constructor(client) {
    this.client = client;
    this.sessions = new CollaborationSessionsResource(client);
  }
}

