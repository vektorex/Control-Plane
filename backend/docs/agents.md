# Governed AI Agent Runtime & Multi-Agent Teams (STEP 40)

## 1. Overview & Architecture

Step 40 introduces **AI Agents** and **Multi-Agent Teams** as first-class, strictly governed execution principals within the AI Work Layer platform. 

An agent is **not** an unconstrained chatbot or autonomous daemon. Every agent execution is bounded, deterministic, policy-enforced, and auditable. Agents are treated as **untrusted principals** that can only execute work explicitly authorized through declarative capability policies, budget envelopes, execution limits, data governance boundaries, and Human-in-the-Loop (HITL) gates.

```
                                  +---------------------------------------+
                                  | Human Principal / Client / API Token   |
                                  +-------------------+-------------------+
                                                      |
                                                      v
                                  +---------------------------------------+
                                  |       Tenant / RBAC Authorization     |
                                  +-------------------+-------------------+
                                                      |
                                                      v
                                  +---------------------------------------+
                                  |       Agent Registry & Versioning     |
                                  |       (Immutable AgentVersion)        |
                                  +-------------------+-------------------+
                                                      |
                                                      v
                  +-----------------------------------------------------------------------+
                  |                             AgentRuntime                              |
                  |                                                                       |
                  |  +---------------------+  +--------------------+  +----------------+  |
                  |  |    AgentIdentity    |  | Effective Policies |  | Governance &   |  |
                  |  |  (Agent, Run, Dep)  |  | (Caps, Budget, Lim)|  | HITL Gates     |  |
                  |  +---------------------+  +--------------------+  +----------------+  |
                  |                                                                       |
                  |  +---------------------+  +--------------------+  +----------------+  |
                  |  | Memory / Knowledge  |  | Bounded AIGateway  |  | Event Bus &    |  |
                  |  | Scope Enforcement   |  | Model Execution    |  | Telemetry / SSE|  |
                  |  +---------------------+  +--------------------+  +----------------+  |
                  +-----------------------------------+-----------------------------------+
                                                      |
                                                      v
                               +---------------------------------------------+
                               |         Multi-Agent Team Coordinator        |
                               |  - Team Planner (Bounded Stages)            |
                               |  - Inter-Agent Messaging (AgentMessage)     |
                               |  - Evidence & Conflict Arbitration          |
                               |  - Final Synthesis & Human Sign-off         |
                               +---------------------------------------------+
```

---

## 2. Agent Identity & Principles

### Invariant: Agents Never Impersonate Humans
Each agent execution receives an immutable `AgentIdentity`:
- `agent_id`: Stable UUID of the agent record.
- `workspace_id`: Tenant boundary (cross-tenant access is strictly denied).
- `project_id`: Optional project scope.
- `agent_version_id`: Exact immutable version executed.
- `execution_id`: UUID of the current run (`AgentRun`).
- `parent_agent_id`: Optional UUID if invoked via sub-agent delegation.
- `delegated_by`: Principal who authorized delegation.
- `is_agent = True`, `is_human = False`.

The platform distinctly categorizes actors as:
1. `HUMAN`: Authenticated user session.
2. `AI AGENT`: Autonomous principal operating within granted capability boundaries.
3. `SYSTEM`: Internal scheduler or background job queue.

---

## 3. Agent Lifecycle

Agents and Teams transition through controlled lifecycle states:
- `draft`: Configuration phase; versions can be created and tested.
- `active`: Validated and published version ready for execution.
- `paused`: Temporarily suspended from receiving new runs or participating in teams.
- `disabled`: Blocked by administrator or security policy.
- `archived`: Read-only historical retention.

State transitions emit audit events (`agent.activated`, `agent.paused`, etc.) and enforce policy validation.

---

## 4. Declarative Capabilities

Agents possess **zero ambient permissions**. All operations require an explicitly granted capability from the following declarative set:

| Capability | Description |
| :--- | :--- |
| `task_execute` | Execute single bounded analytical or generative tasks. |
| `workflow_run` | Trigger execution of approved workflow definitions. |
| `workflow_create_draft` | Create draft workflows for human inspection. |
| `workflow_edit_draft` | Modify existing draft workflows. |
| `retrieve` | Retrieve context from search indexes. |
| `memory_read` | Read from authorized memory scopes. |
| `memory_write` | Persist findings to agent-scoped memory (requires policy approval). |
| `knowledge_read` | Query authorized documents and knowledge graphs. |
| `document_read` | Inspect permitted document artifacts. |
| `artifact_read` | Read workspace artifacts. |
| `artifact_create` | Produce new immutable workspace artifacts. |
| `tool_use` | Invoke permitted tool definitions. |
| `connector_read` | Read untrusted data from authorized external connectors. |
| `prompt_use` | Reference managed prompt templates. |
| `evaluation_run` | Execute factual evaluation metrics. |
| `replay_run` | Run dry-run replay simulations. |
| `collaboration_comment` | Post labeled agent commentary in shared rooms. |
| `collaboration_assign` | Create task assignments in collaboration sessions. |
| `agent_delegate` | Sub-delegate bounded work to permitted child agents. |

---

## 5. Effective Permission Evaluation

Every action initiated by an agent must pass the composite evaluation chain:
```
Effective Permission = RBAC(User) ∩ GovernancePolicy ∩ AgentCapabilityPolicy ∩ HITLPolicy ∩ ResourceScope
```
- **Most Restrictive Wins**: If the human user has permission but the agent's capability policy denies it $\rightarrow$ **DENY**.
- **No Self-Privilege Escalation**: Agents cannot modify their own capability policies or assign permissions.
- **No Self-Approval**: Agents cannot approve their own HITL requests.

---

## 6. Execution Policies & Operational Limits

Agent executions are constrained by conservative operational boundaries:
- `max_steps`: Default 20 steps per run (hard stop prevents unbounded loops).
- `max_iterations`: Default 10 planning/reasoning cycles.
- `max_delegations`: Default 3 sub-agent delegations.
- `max_parallel_agents`: Default 3 concurrent executions.
- `max_runtime_seconds`: Default 300 seconds timeout.
- `max_tool_calls`: Default 15 tool invocations per run.
- `max_connector_calls`: Default 5 connector calls per run.
- `max_cost`: Default $1.00 USD cost ceiling per run.

When limits are reached, the runtime pauses or gracefully completes with partial results rather than silently continuing or overspending.

---

## 7. Bounded Delegation Safety

Agents may only delegate to child agents explicitly registered and permitted in their policy.

### Delegation Invariants:
1. **Capability Subsetting**: A child agent can never receive broader capabilities than its parent ($Caps_{child} \subseteq Caps_{parent}$).
2. **Budget Inheritance**: The child's budget allocation is subtracted from the parent's remaining reservation ($Cost_{child} \le RemainingBudget_{parent}$).
3. **Bounded Depth**: Maximum delegation depth is bounded to **2** by default (A $\rightarrow$ B $\rightarrow$ C is the maximum permitted chain).
4. **Cycle Detection**: Any delegation chain containing a duplicate agent ($A \rightarrow B \rightarrow A$) is detected and rejected with `DelegationCycleDetectedError`.

---

## 8. Multi-Agent Teams

Teams assemble specialized agents to accomplish complex objectives under coordinated oversight.

### Team Roles:
- `lead`: Orchestrates execution stages and reviews specialist handoffs.
- `researcher`: Conducts contextual search, retrieval, and document reading.
- `analyst`: Evaluates data consistency and correlates structured findings.
- `builder`: Generates code or workflow drafts.
- `reviewer`: Audits outputs against policies and checks citations.
- `specialist`: Executes domain-specific tools.
- `executor`: Carries out bounded operational tasks.

*Note: Roles guide coordination flow, not authority. True authority derives exclusively from policies.*

### Inter-Agent Messaging (`AgentMessage`):
Agents communicate via structured messages:
- `task_assignment`
- `task_result`
- `question` / `answer`
- `status_update`
- `handoff`
- `review`
- `correction`
- `final_result`

**Messages are data context, never executable instructions.** Agent messages cannot bypass policies or trick other agents into privilege escalation.

---

## 9. Conflict Handling & Evidence-Based Arbitration

Multi-agent interactions frequently generate conflicting findings. The runtime manages conflicts through `AgentConflict`:
- **States**: `open`, `resolved_by_evidence`, `resolved_by_review`, `resolved_by_human`, `unresolved`.
- **Arbitration Principle**: Conflicts are not resolved based on model authority or agent role. Resolution requires verifying evidence citations or escalating to a human administrator via HITL.

---

## 10. Governance, HITL, & Security

1. **Untrusted Principal Principle**: External connector outputs, tool responses, and agent messages are treated as untrusted and screened for prompt injection.
2. **Mandatory HITL Gates**:
   - External connector writes (e.g. committing GitHub PRs, external API calls).
   - High-cost execution runs exceeding budget thresholds.
   - Destructive database or artifact operations.
   - Material unresolved team conflicts.
3. **Tenant Isolation**: All queries enforce tenant workspace ID filters. Cross-tenant access is blocked at the repository and database layer.

---

## 11. Replay & Reproducibility

Every `AgentRun` records comprehensive reproducibility metadata:
- Agent and team version IDs.
- Model snapshot and temperature settings.
- Exact input snapshot and prompt hashes.
- Tool invocation logs and connector payloads.
- Context sources and memory IDs consulted.
- Governance decisions and HITL records.

**Replay is dry-run by default.** Any external side-effects require fresh human approval before re-execution.

---

## 12. Public API Reference

All public endpoints are authenticated with tenant API keys and enforce granular OAuth/Developer Platform scopes.

| Method | Endpoint | Required Scope | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/agents` | `agents:write` | Create a new agent definition. |
| `GET` | `/api/v1/agents` | `agents:read` | List agents within workspace. |
| `GET` | `/api/v1/agents/{id}` | `agents:read` | Get agent details and current version. |
| `PATCH` | `/api/v1/agents/{id}` | `agents:write` | Update agent metadata. |
| `DELETE` | `/api/v1/agents/{id}` | `agents:write` | Archive agent. |
| `POST` | `/api/v1/agents/{id}/versions` | `agents:write` | Create new draft version. |
| `POST` | `/api/v1/agents/{id}/publish` | `agents:write` | Publish and lock version immutability. |
| `POST` | `/api/v1/agents/{id}/activate` | `agents:write` | Transition agent status to active. |
| `POST` | `/api/v1/agents/{id}/pause` | `agents:write` | Suspend agent execution. |
| `POST` | `/api/v1/agents/{id}/runs` | `agents:execute` | Launch bounded agent run. |
| `GET` | `/api/v1/agents/{id}/runs` | `agents:read` | List agent runs. |
| `GET` | `/api/v1/agent-runs/{run_id}` | `agents:read` | Get run telemetry and results. |
| `GET` | `/api/v1/agent-runs/{run_id}/trace` | `agents:read` | Get observability trace for run. |
| `GET` | `/api/v1/agent-runs/{run_id}/replay` | `agents:execute` | Generate dry-run replay metadata. |
| `POST` | `/api/v1/agents/{id}/delegate` | `agents:execute` | Initiate sub-agent delegation. |
| `POST` | `/api/v1/agent-teams` | `agent_teams:write` | Create multi-agent team. |
| `GET` | `/api/v1/agent-teams` | `agent_teams:read` | List multi-agent teams. |
| `GET` | `/api/v1/agent-teams/{id}` | `agent_teams:read` | Get team details and roster. |
| `POST` | `/api/v1/agent-teams/{id}/runs` | `agent_teams:execute` | Launch coordinated team execution. |
| `GET` | `/api/v1/agent-teams/{id}/runs` | `agent_teams:read` | List team execution history. |
| `GET` | `/api/v1/agent-team-runs/{run_id}` | `agent_teams:read` | Inspect team stages, messages, & conflicts. |

---

## 13. SDK Usage Examples

### JavaScript SDK
```javascript
import { AIWorkLayerClient } from "@ai-work-layer/sdk";

const client = new AIWorkLayerClient({
  apiKey: process.env.AI_WORK_LAYER_API_KEY,
  workspaceId: "ws-12345",
});

// 1. Single Agent Execution
const run = await client.agents.run("agent-researcher-01", {
  input: { task: "Analyze recent cloud cost trends across regions" },
  execution_policy_override: { max_steps: 10 },
});
console.log(`Agent Run ID: ${run.id}, Status: ${run.status}`);

// 2. Launch Multi-Agent Team Run
const teamRun = await client.agentTeams.run("team-audit-squad", {
  objective: "Conduct security review and compliance check on release candidate v2.4",
});
console.log(`Team Run ID: ${teamRun.id}, Stage: ${teamRun.status}`);
```

### Python SDK
```python
from ai_work_layer import AIWorkLayerClient

client = AIWorkLayerClient(
    api_key="sk_live_...",
    workspace_id="ws-12345"
)

# Create and Activate Agent
agent = client.agents.create(
    name="Financial Analyst",
    purpose="Perform quarterly budget variance analysis",
    capabilities=["task_execute", "document_read", "artifact_create"],
    instructions="Review financial tables and report standard deviation variances.",
    preferred_model="gpt-4o-mini"
)

client.agents.activate(agent["id"])

# Execute Bounded Task
run = client.agents.run(agent["id"], input_data={"fiscal_year": 2026, "quarter": "Q3"})
print(f"Result Output: {run['output']['text']}")
```

---

## 14. Concrete Workflow Configurations

### Example 1: Agent with Document Retrieval & Tool Use
```json
{
  "name": "DocuSearcher",
  "purpose": "Index search and document summarization",
  "capability_policy": ["task_execute", "knowledge_read", "retrieve", "tool_use"],
  "knowledge_policy": {
    "allowed_context_sources": ["workspace_docs", "compliance_repo"],
    "max_context_tokens": 4000
  },
  "execution_policy": {
    "max_steps": 12,
    "max_cost": 0.30
  }
}
```

### Example 2: Researcher + Reviewer Team with Mandatory HITL Gate
```json
{
  "name": "Audit & Review Squad",
  "objective": "Research vulnerabilities and produce verified security advisories",
  "members": [
    {
      "agent_id": "agent-researcher",
      "role": "researcher",
      "responsibilities": "Scan knowledge bases and compile draft vulnerability report."
    },
    {
      "agent_id": "agent-reviewer",
      "role": "reviewer",
      "responsibilities": "Validate CVE citations and audit against policy."
    }
  ],
  "coordination_policy": {
    "mode": "hierarchical",
    "max_parallel_agents": 2
  },
  "approval_policy": {
    "require_human_approval_for_synthesis": true
  }
}
```
