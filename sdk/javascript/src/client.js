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
    this.agents = new AgentsResource(this);
    this.agentTeams = new AgentTeamsResource(this);
    this.simulations = new SimulationsResource(this);
    this.scenarios = new ScenariosResource(this);
    this.suites = new SuitesResource(this);
    this.objectives = new ObjectivesResource(this);
    this.outcomes = new OutcomesResource(this);
    this.decisions = new DecisionsResource(this);
    this.workPlans = new WorkPlansResource(this);
    this.planningScenarios = new PlanningScenariosResource(this);
    this.resources = new WorkResourcesResource(this);
    this.capacity = new CapacityResource(this);
    this.reservations = new ReservationsResource(this);
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

export class AgentsResource {
  constructor(client) {
    this.client = client;
  }

  async list(params = {}) {
    const query = new URLSearchParams();
    if (params.projectId) query.set("project_id", params.projectId);
    if (params.status) query.set("status", params.status);
    if (params.limit) query.set("limit", params.limit);
    if (params.offset) query.set("offset", params.offset);
    const qs = query.toString();
    return this.client.request("GET", `/agents${qs ? `?${qs}` : ""}`);
  }

  async get(agentId) {
    return this.client.request("GET", `/agents/${agentId}`);
  }

  async create(data, options = {}) {
    return this.client.request("POST", "/agents", {
      body: data,
      idempotencyKey: options.idempotencyKey,
    });
  }

  async update(agentId, data, options = {}) {
    return this.client.request("PATCH", `/agents/${agentId}`, {
      body: data,
      idempotencyKey: options.idempotencyKey,
    });
  }

  async delete(agentId) {
    return this.client.request("DELETE", `/agents/${agentId}`);
  }

  async createVersion(agentId, data, options = {}) {
    return this.client.request("POST", `/agents/${agentId}/versions`, {
      body: data,
      idempotencyKey: options.idempotencyKey,
    });
  }

  async publish(agentId, versionId = null) {
    const query = versionId ? `?version_id=${encodeURIComponent(versionId)}` : "";
    return this.client.request("POST", `/agents/${agentId}/publish${query}`);
  }

  async activate(agentId) {
    return this.client.request("POST", `/agents/${agentId}/activate`);
  }

  async pause(agentId) {
    return this.client.request("POST", `/agents/${agentId}/pause`);
  }

  async run(agentId, data = {}, options = {}) {
    return this.client.request("POST", `/agents/${agentId}/runs`, {
      body: data,
      idempotencyKey: options.idempotencyKey,
    });
  }

  async listRuns(agentId, params = {}) {
    const query = new URLSearchParams();
    if (params.status) query.set("status", params.status);
    if (params.limit) query.set("limit", params.limit);
    if (params.offset) query.set("offset", params.offset);
    const qs = query.toString();
    return this.client.request("GET", `/agents/${agentId}/runs${qs ? `?${qs}` : ""}`);
  }

  async getRun(runId) {
    return this.client.request("GET", `/agent-runs/${runId}`);
  }

  async delegate(agentId, data, options = {}) {
    return this.client.request("POST", `/agents/${agentId}/delegate`, {
      body: data,
      idempotencyKey: options.idempotencyKey,
    });
  }

  async trace(runId) {
    return this.client.request("GET", `/agent-runs/${runId}/trace`);
  }

  async replay(runId) {
    return this.client.request("GET", `/agent-runs/${runId}/replay`);
  }
}

export class AgentTeamsResource {
  constructor(client) {
    this.client = client;
  }

  async list(params = {}) {
    const query = new URLSearchParams();
    if (params.projectId) query.set("project_id", params.projectId);
    if (params.status) query.set("status", params.status);
    if (params.limit) query.set("limit", params.limit);
    if (params.offset) query.set("offset", params.offset);
    const qs = query.toString();
    return this.client.request("GET", `/agent-teams${qs ? `?${qs}` : ""}`);
  }

  async get(teamId) {
    return this.client.request("GET", `/agent-teams/${teamId}`);
  }

  async create(data, options = {}) {
    return this.client.request("POST", "/agent-teams", {
      body: data,
      idempotencyKey: options.idempotencyKey,
    });
  }

  async update(teamId, data, options = {}) {
    return this.client.request("PATCH", `/agent-teams/${teamId}`, {
      body: data,
      idempotencyKey: options.idempotencyKey,
    });
  }

  async run(teamId, data = {}, options = {}) {
    return this.client.request("POST", `/agent-teams/${teamId}/runs`, {
      body: data,
      idempotencyKey: options.idempotencyKey,
    });
  }

  async listRuns(teamId, params = {}) {
    const query = new URLSearchParams();
    if (params.limit) query.set("limit", params.limit);
    if (params.offset) query.set("offset", params.offset);
    const qs = query.toString();
    return this.client.request("GET", `/agent-teams/${teamId}/runs${qs ? `?${qs}` : ""}`);
  }

  async getRun(runId) {
    return this.client.request("GET", `/agent-team-runs/${runId}`);
  }
}

export class SimulationsResource {
  constructor(client) {
    this.client = client;
  }

  async create(data, options = {}) {
    return this.client.request("POST", "/simulations", {
      body: data,
      idempotencyKey: options.idempotencyKey,
    });
  }

  async get(simulationId) {
    return this.client.request("GET", `/simulations/${simulationId}`);
  }

  async list(params = {}) {
    const query = new URLSearchParams();
    if (params.projectId) query.set("project_id", params.projectId);
    if (params.targetType) query.set("target_type", params.targetType);
    if (params.targetId) query.set("target_id", params.targetId);
    if (params.status) query.set("status", params.status);
    if (params.limit) query.set("limit", params.limit);
    if (params.offset) query.set("offset", params.offset);
    const qs = query.toString();
    return this.client.request("GET", `/simulations${qs ? `?${qs}` : ""}`);
  }

  async update(simulationId, data, options = {}) {
    return this.client.request("PATCH", `/simulations/${simulationId}`, {
      body: data,
      idempotencyKey: options.idempotencyKey,
    });
  }

  async createVersion(simulationId, data, options = {}) {
    return this.client.request("POST", `/simulations/${simulationId}/versions`, {
      body: data,
      idempotencyKey: options.idempotencyKey,
    });
  }

  async run(simulationId, data = {}, options = {}) {
    return this.client.request("POST", `/simulations/${simulationId}/run`, {
      body: data,
      idempotencyKey: options.idempotencyKey,
    });
  }

  async listRuns(simulationId, params = {}) {
    const query = new URLSearchParams();
    if (params.status) query.set("status", params.status);
    if (params.limit) query.set("limit", params.limit);
    if (params.offset) query.set("offset", params.offset);
    const qs = query.toString();
    return this.client.request("GET", `/simulations/${simulationId}/runs${qs ? `?${qs}` : ""}`);
  }

  async getRun(runId) {
    return this.client.request("GET", `/simulation-runs/${runId}`);
  }

  async getTrace(runId) {
    return this.client.request("GET", `/simulation-runs/${runId}/trace`);
  }

  async getReport(runId) {
    return this.client.request("GET", `/simulation-runs/${runId}/report`);
  }

  async getSideEffects(runId) {
    return this.client.request("GET", `/simulation-runs/${runId}/side-effects`);
  }

  async getAssertions(runId) {
    return this.client.request("GET", `/simulation-runs/${runId}/assertions`);
  }

  async compare(runId, comparisonRunId, options = {}) {
    return this.client.request("POST", `/simulation-runs/${runId}/compare`, {
      body: { comparison_run_id: comparisonRunId },
      idempotencyKey: options.idempotencyKey,
    });
  }
}

export class ScenariosResource {
  constructor(client) {
    this.client = client;
  }

  async create(data, options = {}) {
    return this.client.request("POST", "/simulation-scenarios", {
      body: data,
      idempotencyKey: options.idempotencyKey,
    });
  }

  async get(scenarioId) {
    return this.client.request("GET", `/simulation-scenarios/${scenarioId}`);
  }

  async update(scenarioId, data, options = {}) {
    return this.client.request("PATCH", `/simulation-scenarios/${scenarioId}`, {
      body: data,
      idempotencyKey: options.idempotencyKey,
    });
  }
}

export class SuitesResource {
  constructor(client) {
    this.client = client;
  }

  async create(data, options = {}) {
    return this.client.request("POST", "/simulation-suites", {
      body: data,
      idempotencyKey: options.idempotencyKey,
    });
  }

  async get(suiteId) {
    return this.client.request("GET", `/simulation-suites/${suiteId}`);
  }

  async list(params = {}) {
    const query = new URLSearchParams();
    if (params.targetType) query.set("target_type", params.targetType);
    if (params.targetId) query.set("target_id", params.targetId);
    if (params.limit) query.set("limit", params.limit);
    if (params.offset) query.set("offset", params.offset);
    const qs = query.toString();
    return this.client.request("GET", `/simulation-suites${qs ? `?${qs}` : ""}`);
  }

  async run(suiteId, data = {}, options = {}) {
    return this.client.request("POST", `/simulation-suites/${suiteId}/run`, {
      body: data,
      idempotencyKey: options.idempotencyKey,
    });
  }
}

export class ObjectivesResource {
  constructor(client) {
    this.client = client;
  }

  async create(data, options = {}) {
    return this.client.request("POST", "/objectives", {
      body: data,
      idempotencyKey: options.idempotencyKey,
    });
  }

  async get(objectiveId) {
    return this.client.request("GET", `/objectives/${objectiveId}`);
  }

  async list(params = {}) {
    const query = new URLSearchParams();
    if (params.projectId) query.set("project_id", params.projectId);
    if (params.status) query.set("status", params.status);
    if (params.objectiveType) query.set("objective_type", params.objectiveType);
    if (params.limit) query.set("limit", params.limit);
    if (params.offset) query.set("offset", params.offset);
    const qs = query.toString();
    return this.client.request("GET", `/objectives${qs ? `?${qs}` : ""}`);
  }

  async update(objectiveId, data) {
    return this.client.request("PATCH", `/objectives/${objectiveId}`, { body: data });
  }

  async delete(objectiveId) {
    return this.client.request("DELETE", `/objectives/${objectiveId}`);
  }

  async getHealth(objectiveId) {
    return this.client.request("GET", `/objectives/${objectiveId}/health`);
  }

  async getWorkMap(objectiveId) {
    return this.client.request("GET", `/objectives/${objectiveId}/work-map`);
  }
}

export class OutcomesResource {
  constructor(client) {
    this.client = client;
  }

  async create(data, options = {}) {
    return this.client.request("POST", "/outcomes", {
      body: data,
      idempotencyKey: options.idempotencyKey,
    });
  }

  async get(outcomeId) {
    return this.client.request("GET", `/outcomes/${outcomeId}`);
  }

  async list(params = {}) {
    const query = new URLSearchParams();
    if (params.projectId) query.set("project_id", params.projectId);
    if (params.objectiveId) query.set("objective_id", params.objectiveId);
    if (params.status) query.set("status", params.status);
    if (params.outcomeType) query.set("outcome_type", params.outcomeType);
    if (params.limit) query.set("limit", params.limit);
    if (params.offset) query.set("offset", params.offset);
    const qs = query.toString();
    return this.client.request("GET", `/outcomes${qs ? `?${qs}` : ""}`);
  }

  async addEvidence(outcomeId, data) {
    return this.client.request("POST", `/outcomes/${outcomeId}/evidence`, { body: data });
  }

  async verify(outcomeId, data = {}) {
    return this.client.request("POST", `/outcomes/${outcomeId}/verify`, { body: data });
  }

  async dispute(outcomeId, data = {}) {
    return this.client.request("POST", `/outcomes/${outcomeId}/dispute`, { body: data });
  }

  async getImpact(outcomeId) {
    return this.client.request("GET", `/outcomes/${outcomeId}/impact`);
  }

  async getWork(outcomeId) {
    return this.client.request("GET", `/outcomes/${outcomeId}/work`);
  }

  async getGraph(outcomeId) {
    return this.client.request("GET", `/outcomes/${outcomeId}/graph`);
  }
}

export class DecisionsResource {
  constructor(client) {
    this.client = client;
  }

  async create(data, options = {}) {
    return this.client.request("POST", "/decisions", {
      body: data,
      idempotencyKey: options.idempotencyKey,
    });
  }

  async get(decisionId) {
    return this.client.request("GET", `/decisions/${decisionId}`);
  }

  async list(params = {}) {
    const query = new URLSearchParams();
    if (params.projectId) query.set("project_id", params.projectId);
    if (params.objectiveId) query.set("objective_id", params.objectiveId);
    if (params.outcomeId) query.set("outcome_id", params.outcomeId);
    if (params.status) query.set("status", params.status);
    if (params.limit) query.set("limit", params.limit);
    if (params.offset) query.set("offset", params.offset);
    const qs = query.toString();
    return this.client.request("GET", `/decisions${qs ? `?${qs}` : ""}`);
  }

  async approve(decisionId) {
    return this.client.request("POST", `/decisions/${decisionId}/approve`);
  }

  async reject(decisionId, reason = null) {
    const query = reason ? `?reason=${encodeURIComponent(reason)}` : "";
    return this.client.request("POST", `/decisions/${decisionId}/reject${query}`);
  }
}

export class WorkPlansResource {
  constructor(client) {
    this.client = client;
  }

  async create(data, options = {}) {
    return this.client.request("POST", "/work-plans", {
      body: data,
      idempotencyKey: options.idempotencyKey,
    });
  }

  async get(planId) {
    return this.client.request("GET", `/work-plans/${planId}`);
  }

  async list(params = {}) {
    const query = new URLSearchParams();
    if (params.projectId) query.set("project_id", params.projectId);
    if (params.objectiveId) query.set("objective_id", params.objectiveId);
    if (params.status) query.set("status", params.status);
    if (params.limit) query.set("limit", params.limit);
    if (params.offset) query.set("offset", params.offset);
    const qs = query.toString();
    return this.client.request("GET", `/work-plans${qs ? `?${qs}` : ""}`);
  }

  async update(planId, data) {
    return this.client.request("PATCH", `/work-plans/${planId}`, { body: data });
  }

  async generate(planId, data = {}) {
    return this.client.request("POST", `/work-plans/${planId}/plan`, { body: data });
  }

  async validate(planId) {
    return this.client.request("POST", `/work-plans/${planId}/validate`);
  }

  async activate(planId) {
    return this.client.request("POST", `/work-plans/${planId}/activate`);
  }

  async pause(planId) {
    return this.client.request("POST", `/work-plans/${planId}/pause`);
  }

  async getDependencies(planId) {
    return this.client.request("GET", `/work-plans/${planId}/dependencies`);
  }

  async getResources(planId) {
    return this.client.request("GET", `/work-plans/${planId}/resources`);
  }

  async getConflicts(planId) {
    return this.client.request("GET", `/work-plans/${planId}/conflicts`);
  }

  async getBlockers(planId) {
    return this.client.request("GET", `/work-plans/${planId}/blockers`);
  }
}

export class PlanningScenariosResource {
  constructor(client) {
    this.client = client;
  }

  async create(data, options = {}) {
    return this.client.request("POST", "/planning-scenarios", {
      body: data,
      idempotencyKey: options.idempotencyKey,
    });
  }

  async get(scenarioId) {
    return this.client.request("GET", `/planning-scenarios/${scenarioId}`);
  }

  async run(scenarioId) {
    return this.client.request("POST", `/planning-scenarios/${scenarioId}/run`);
  }
}

export class WorkResourcesResource {
  constructor(client) {
    this.client = client;
  }

  async list(params = {}) {
    const query = new URLSearchParams();
    if (params.resourceType) query.set("resource_type", params.resourceType);
    if (params.status) query.set("status", params.status);
    const qs = query.toString();
    return this.client.request("GET", `/resources${qs ? `?${qs}` : ""}`);
  }

  async get(resourceId) {
    return this.client.request("GET", `/resources/${resourceId}`);
  }

  async getCapacity(resourceId) {
    return this.client.request("GET", `/resources/${resourceId}/capacity`);
  }
}

export class CapacityResource {
  constructor(client) {
    this.client = client;
  }

  async getForecast(horizonDays = 14) {
    return this.client.request("GET", `/planning/forecast?horizon_days=${horizonDays}`);
  }

  async getWorkload() {
    return this.client.request("GET", "/planning/workload");
  }
}

export class ReservationsResource {
  constructor(client) {
    this.client = client;
  }

  async create(data, options = {}) {
    return this.client.request("POST", "/capacity-reservations", {
      body: data,
      idempotencyKey: options.idempotencyKey,
    });
  }

  async list(resourceId = null) {
    const query = resourceId ? `?resource_id=${encodeURIComponent(resourceId)}` : "";
    return this.client.request("GET", `/capacity-reservations${query}`);
  }
}


