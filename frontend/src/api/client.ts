import axios from "axios";

const BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

const api = axios.create({ baseURL: BASE_URL });

// inject token on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// auth
export const login = (username: string, password: string) =>
  api.post("/auth/login", { username, password });

export const register = (username: string, password: string) =>
  api.post("/auth/register", { username, password });

// agents
export const runAgent = (task: string, agentType: string, sessionId?: string) =>
  api.post("/agent/run", { task, agent_type: agentType, session_id: sessionId });

// pipeline
export const runPipeline = (task: string, requireApproval: boolean = true) =>
  api.post("/pipeline/run", { task, require_approval: requireApproval });

export const getPendingApprovals = () => api.get("/pipeline/approvals");

export const decideApproval = (approvalId: string, approved: boolean, reason?: string) =>
  api.post(`/pipeline/approvals/${approvalId}/decide`, { approved, reason });

// eval
export const getEvalMetrics = () => api.get("/eval/metrics");

export const runRegressionV2 = () =>
  api.post("/eval/v2/regression?output_format=json");

// memory
export const getMemoryStats = () => api.get("/memory/stats");

export const recallMemory = (query: string) =>
  api.get(`/memory/recall?query=${encodeURIComponent(query)}`);

// registry
export const getTools = () => api.get("/registry/tools");
export const getAgents = () => api.get("/registry/agents");

// rag
export const ingestDocument = (text: string, source: string) =>
  api.post("/rag/ingest", { text, source });

export const retrieveContext = (query: string, topK: number = 5) =>
  api.post("/rag/retrieve", { query, top_k: topK });