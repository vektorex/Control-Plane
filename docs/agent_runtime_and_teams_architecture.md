# Governed AI Agent Runtime and Multi-Agent Teams Architecture (STEP 40)

## System Overview
Step 40 implements the Governed AI Agent Runtime and Multi-Agent Teams layer. This architecture establishes AI agents as first-class, bounded execution principals that execute tasks strictly within established platform constraints.

### Core Architecture Components

1. **Agent Domain & Registry (`backend/app/services/agents/`)**:
   - `Agent`: Core entity bounded strictly by tenant workspace.
   - `AgentVersion`: Immutable configuration snapshot with instructions, capability policy, model policy, memory policy, knowledge policy, execution policy, evaluation policy, and budget policy.
   - `AgentRegistry`: Resolves immutable execution configurations and validates capability boundaries.

2. **Agent Identity (`identity.py`)**:
   - Distinct, unforgeable `AgentIdentity` propagated to telemetry, audit, jobs, HITL, tools, and collaboration sessions.
   - Explicitly establishes `is_agent = True`, `is_human = False`. Agents can never impersonate a human collaborator.

3. **Effective Permissions & Governance (`permissions.py`, `policies.py`)**:
   - Evaluates RBAC + Governance + Agent Capability Policy + HITL Policy + Scope.
   - Enforces the principle of most-restrictive permissions.
   - Prohibits self-approval and self-modification of capabilities.

4. **Delegation Engine (`delegation.py`, `validators.py`)**:
   - Enforces bounded delegation depth (maximum 2 by default).
   - Detects and rejects circular delegation ($A \to B \to A$).
   - Inherits and constrains budgets and capabilities from parent to child.

5. **Multi-Agent Team Orchestration (`team.py`, `planner.py`, `messages.py`)**:
   - Coordinates teams of specialized agents with distinct operational roles (`lead`, `researcher`, `analyst`, `builder`, `reviewer`, `specialist`, `executor`).
   - Normalizes peer communications into read-only `AgentMessage` data structures that cannot bypass system policies.
   - Evidence-based conflict arbitration (`AgentConflict`) preventing subjective bias.

6. **Durable Jobs & Event Bus Integration**:
   - Agent runs and team executions run durably on the Step 24 Job Queue (`agent_run`, `agent_delegation`, `agent_team_run`, `agent_evaluation`).
   - All state transitions emit sequenced events to the Step 26 Event Bus (`agent.run.started`, `agent.team.conflict.detected`, etc.).
