# Step 20: AI Task Intelligence Architecture

## 1. Overview & Core Mission

The **AI Task Intelligence Layer** analyzes an incoming task to determine its factual execution requirements and produces a bounded, policy-enforced execution configuration for the existing Orchestrator.

The intelligence layer systematically and intelligently answers:
> *"What does this task actually need?"*

Possible execution requirements resolved:
- **Direct generation**: Direct LLM synthesis with no retrieval, tools, or external services.
- **Memory**: Persistent memory retrieval and relevance.
- **Documents**: Workspace document grounding and retrieval.
- **Web search**: Live internet grounding via web search tools.
- **Connectors**: External systems integration (e.g. GitHub repositories, issues, PRs).
- **Tools**: Server-registered tool execution.
- **Structured output**: Strict JSON schema or typed formatting.
- **Multiple retrieval queries**: Query expansion for broad or complex comparative topics.
- **Evaluation**: Verification, grounding checks, and revision loops.
- **Human approval**: HITL gating for state-changing or external actions.
- **Specific model capabilities**: Requirements for `vision`, `long_context`, `tools`, `structured_output`, `streaming`.
- **Workflow execution**: Predefined multi-step orchestration workflows.

> [!IMPORTANT]
> **Authoritative Boundary Principle**:
> **Task Intelligence recommends execution requirements; existing execution services remain authoritative.**
> Task Intelligence does NOT execute tools, does NOT directly retrieve documents, does NOT bypass policy or HITL approvals, does NOT choose unauthorized models, and does NOT modify memory directly. All decisions are validated and enforced by server-side policies.

---

## 2. End-to-End Pipeline & Architecture Flow

```mermaid
flowchart TD
    UserTask["Incoming Task (Instructions, Context, Options)"] --> TI["TaskIntelligenceService"]
    
    subgraph TI_Engine["Task Intelligence Engine"]
        TI --> Mode{"Analyzer Mode"}
        Mode -->|Deterministic| Rules["RuleBasedTaskAnalyzer"]
        Mode -->|LLM| LLMA["LLMTaskAnalyzer (via AIGateway)"]
        Mode -->|Hybrid (Default)| Hybrid["HybridTaskAnalyzer"]
        
        Hybrid --> Rules
        Rules --> ConfCalc{"Confidence & Ambiguity Check"}
        ConfCalc -->|High Confidence| DeterministicPlan["Deterministic Requirements"]
        ConfCalc -->|Ambiguous Signals| LLMA
        
        LLMA --> Fallback{"Valid LLM Response?"}
        Fallback -->|Yes| LLMPlan["LLM Proposed Requirements"]
        Fallback -->|Timeout / Invalid / Circuit Open| RulesFallback["Fallback to Deterministic Heuristics"]
    end
    
    DeterministicPlan --> Resolver["TaskRequirementResolver"]
    LLMPlan --> Resolver
    RulesFallback --> Resolver
    
    subgraph Policy_Layer["Validation & Precedence Layer"]
        Resolver --> Precedence["Enforce Precedence Rules:\n1. Security Policy (Highest)\n2. Explicit User Override\n3. Application Policy\n4. Deterministic Invariants\n5. LLM Proposals (Lowest)"]
        Precedence --> Validator["ExecutionRequirementsValidator"]
        Validator -->|Check Constraints, Top-K, Permissions, HITL| BoundedConfig["ExecutionRequirements"]
    end
    
    BoundedConfig --> Orchestrator["Orchestrator Pipeline"]
    
    subgraph Execution_Services["Authoritative Execution Services"]
        Orchestrator --> ContextEngine["ContextEngine"]
        Orchestrator --> RetrievalRouter["RetrievalRouter"]
        Orchestrator --> ToolExecutor["ToolRegistry & ToolExecutor"]
        Orchestrator --> ModelRouter["ModelRouter & AIGateway"]
        Orchestrator --> EvaluationEngine["EvaluationEngine"]
        Orchestrator --> HITL["ApprovalPolicyEngine (HITL)"]
    end
    
    Execution_Services --> FinalOutput["Safe Bounded Output + Run Telemetry"]
```

---

## 3. Analyzer Implementations

The architecture defines three analyzer implementations under `backend/app/services/task_intelligence/`:

### 3.1. RuleBasedTaskAnalyzer (`rules.py`)
Deterministic, fast, zero-token signal detection with conservative heuristics:
- **Web Search**: Queries referencing `"search the web"`, `"latest news"`, `"current market"`, `"today"`, etc.
- **Documents**: Direct references like `"from my documents"`, `"in the uploaded pdf"`, `"search codebase"`.
- **Connectors**: Queries referencing `"from my github"`, `"repository issues"`, `"pull request"`.
- **Structured Output**: Explicit formatting directives like `"return json"`, `"output as a json object"`.
- **Vision**: Tasks requesting `"analyze this image"`, `"inspect diagram"`, `"what is in this photo"`.
- **Memory**: Direct personal context cues like `"remember this"`, `"my usual coding style"`, `"my preferences"`.
- **HITL Candidate**: External mutating actions like `"send email"`, `"create github issue"`, `"delete branch"`.

### 3.2. LLMTaskAnalyzer (`llm_analyzer.py`)
Uses the unified `AIGateway` (`default_ai_gateway`) with:
- Strict Pydantic schema validation (`TaskAnalysis`).
- Strictly non-executable: proposes requirements only.
- Strict bounded token allocation: `TASK_ANALYSIS_MAX_TOKENS = 1000`.
- Timeout bounded: `TASK_ANALYSIS_TIMEOUT_SECONDS = 15.0`.
- Circuit-breaker aware: If gateway is open or fails, immediately falls back to deterministic analysis without failing task execution.
- No chain-of-thought is requested or returned.

### 3.3. HybridTaskAnalyzer (`hybrid.py`)
Production default:
1. Executes `RuleBasedTaskAnalyzer` first.
2. Checks signal density and confidence using `ConfidenceCalculator`.
3. If deterministic signals decisively categorize the task (e.g. obvious web search, explicit document Q&A, simple direct generation), bypasses the LLM to eliminate token cost and latency.
4. Only invokes `LLMTaskAnalyzer` for complex or ambiguous natural language directives.
5. If the LLM analyzer fails, times out, or returns invalid data, automatically falls back to deterministic analysis.

---

## 4. Requirement Merging & Policy Precedence

Requirements are resolved by `TaskRequirementResolver` (`requirements.py`) using strict hierarchical precedence:

```
┌─────────────────────────────────────────────────────────┐
│ 1. Security Policy (Highest - Workspace bounds, admin)   │
├─────────────────────────────────────────────────────────┤
│ 2. Explicit User Override ("Do not search the web")     │
├─────────────────────────────────────────────────────────┤
│ 3. Application Policy (Evaluation strictness, tool caps)│
├─────────────────────────────────────────────────────────┤
│ 4. Deterministic Rule Invariants                        │
├─────────────────────────────────────────────────────────┤
│ 5. LLM Analysis Proposals (Lowest - Untrusted candidate)│
└─────────────────────────────────────────────────────────┘
```

### Precedence Rules:
1. **Explicit User Overrides**: If the user explicitly disables web search (`enable_web_search=False` or `"Do not search the web"`), web search is set to `False`, even if the LLM recommends it.
2. **Security Policy Overrides**: If workspace policy disables tools or external connectors, they cannot be activated by user input or LLM proposals.
3. **No Weakening**: An unvalidated LLM suggestion cannot weaken security or HITL approval policies.
4. **Conservative Fallback**: Ambiguous or uncertain requirements default to safe, non-destructive baselines.

---

## 5. Execution Complexity Classification

Execution complexity is classified factually for execution planning only (never labeled as subjective "quality" or "difficulty"):

| Complexity | Criteria | Typical Pipeline |
| :--- | :--- | :--- |
| **Simple** | Single direct generation with no external tools or retrieval. | Direct LLM Synthesis |
| **Moderate** | Generation requiring single tool, knowledge retrieval, or grounding evaluation. | Retrieval + Generation |
| **Complex** | Multiple knowledge sources, multi-query expansion, tool chaining, revision loops, or workflow. | Multi-Step Orchestrated |

---

## 6. Security Model & Trust Boundaries

1. **Untrusted Inputs**: User input, LLM analysis proposals, external document chunks, and web search results are untrusted.
2. **Zero Direct Execution**: Task Intelligence never executes tools, never calls external connectors, never alters database state, and never performs memory writes.
3. **Authoritative Systems**:
   - Tools are validated and executed solely by `ToolRegistry` and `ToolExecutor`.
   - Connectors are governed by `ConnectorRegistry` and user permissions.
   - Retrieval is executed solely by `RetrievalRouter`.
   - Model selection is routed solely through `ModelRouter` and `AIGateway`.
   - Memory access is governed solely by `MemoryPolicy` and `MemoryRetriever`.
   - Human approvals are gated solely by `ApprovalPolicyEngine`.

---

## 7. Cost Control & Telemetry

- **Cost Optimization**: Deterministic rules run first. Unambiguous simple tasks bypass LLM analysis, eliminating unnecessary token usage and latency.
- **Bounded Resource Limits**: Maximum 1,000 tokens and 15-second timeout for LLM analysis.
- **High Availability**: If the analyzer model experiences rate limiting, circuit breaker trip, or network failure, task intelligence seamlessly falls back to deterministic analysis without blocking execution.
- **Telemetry Integration**: Emits events to the observability engine:
  - `task_analysis_started`
  - `task_analysis_completed`
  - `task_requirement_validation_failed`
- **Privacy**: Raw user instructions and sensitive prompt data are sanitized before telemetry logging.

---

## 8. API Reference

### 8.1. `POST /api/tasks/analyze`
Analyzes raw task text and context without executing:
```json
{
  "task": "Research the latest features in Python 3.13 and summarize in JSON",
  "context": "Focus on free-threaded CPython and JIT compiler.",
  "mode": "auto"
}
```
**Response**:
```json
{
  "analysis": {
    "task_type": "research",
    "intent": "Research recent information about Python 3.13 and output structured format.",
    "suggested_execution_mode": "orchestrated",
    "confidence": 0.92,
    "explanation": "Research task requiring web search grounding, tool execution, and structured output formatting."
  },
  "requirements": {
    "execution_mode": "orchestrated",
    "task_type": "research",
    "retrieval": { "enabled": true, "strategy": "hybrid" },
    "tools": { "enabled": true, "required_tools": ["web_search"] },
    "structured_output": { "enabled": true },
    "evaluation": { "enabled": true, "mode": "standard" },
    "human_approval": { "enabled": false }
  },
  "execution_mode": "orchestrated"
}
```

### 8.2. `POST /api/tasks/preview-execution`
Returns factual execution configuration for an ad-hoc or existing task without executing.

### 8.3. `POST /api/tasks/{task_id}/analyze` and `POST /api/tasks/{task_id}/preview-execution`
Inspects an existing persisted task and resolves its bounded execution requirements.

### 8.4. `POST /api/tasks/{task_id}/run` and `/stream`
Integrates task intelligence prior to execution, validates requirements against workspace policies, and persists `task_type`, `execution_mode`, and `execution_requirements` in the Run's input snapshot.
