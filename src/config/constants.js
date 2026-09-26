export const TASK_STATUSES = {
  PENDING: "PENDING",
  ROUTING: "ROUTING",
  PROCESSING: "PROCESSING",
  COMPLETED: "COMPLETED",
  FAILED: "FAILED",
  CANCELLED: "CANCELLED",
};

export const TASK_PRIORITIES = {
  LOW: "low",
  MEDIUM: "medium",
  HIGH: "high",
  CRITICAL: "critical",
};

export const EXECUTION_MODES = {
  AUTO: "auto",
  FAST: "fast",
  DEEP_REASONING: "deep_reasoning",
  COST_OPTIMIZED: "cost_optimized",
};

export const MODEL_PROVIDERS = [
  { id: "anthropic", name: "Anthropic", status: "ready" },
  { id: "openai", name: "OpenAI", status: "ready" },
  { id: "google", name: "Google Vertex / Gemini", status: "ready" },
  { id: "deepseek", name: "DeepSeek", status: "ready" },
  { id: "local", name: "Local Ollama / vLLM", status: "configured" },
];

export const RETRIEVAL_STRATEGIES = [
  { id: "hybrid_rag", name: "Hybrid Dense + Sparse RAG", description: "Combines vector similarity with BM25 keyword matching" },
  { id: "hierarchical_graph", name: "Knowledge Graph + Hierarchical", description: "Entity relationship mapping for multi-hop synthesis" },
  { id: "direct_context", name: "Direct Window Context", description: "Zero-retrieval direct context insertion" },
];
