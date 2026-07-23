import React, { useState } from "react";
import { runAgent } from "../api/client";
import { Bot, Play, Loader } from "lucide-react";

const AGENT_TYPES = ["planner", "coder", "reviewer", "tester", "researcher", "documenter"];

export const AgentRunner = () => {
  const [task, setTask] = useState("");
  const [agentType, setAgentType] = useState("planner");
  const [output, setOutput] = useState("");
  const [loading, setLoading] = useState(false);
  const [iterations, setIterations] = useState(0);
  const [error, setError] = useState("");

  const handleRun = async () => {
    if (!task.trim()) return;
    setLoading(true);
    setOutput("");
    setError("");
    try {
      const res = await runAgent(task, agentType);
      setOutput(res.data.output);
      setIterations(res.data.iterations);
    } catch (e: any) {
      setError(e.response?.data?.detail || "Agent failed");
    }
    setLoading(false);
  };

  return (
    <div className="p-8">
      <div className="flex items-center gap-3 mb-6">
        <Bot size={24} className="text-primary" />
        <h2 className="text-2xl font-bold text-white">Agent Runner</h2>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-1 space-y-4">
          <div>
            <label className="text-sm text-gray-400 mb-2 block">Agent Type</label>
            <select
              value={agentType}
              onChange={e => setAgentType(e.target.value)}
              className="w-full bg-dark border border-border rounded-lg px-4 py-3 text-white text-sm focus:outline-none focus:border-primary"
            >
              {AGENT_TYPES.map(t => (
                <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-sm text-gray-400 mb-2 block">Task</label>
            <textarea
              value={task}
              onChange={e => setTask(e.target.value)}
              placeholder="Describe what you want the agent to do..."
              rows={6}
              className="w-full bg-dark border border-border rounded-lg px-4 py-3 text-white text-sm focus:outline-none focus:border-primary resize-none"
            />
          </div>

          <button
            onClick={handleRun}
            disabled={loading || !task.trim()}
            className="w-full flex items-center justify-center gap-2 bg-primary hover:bg-indigo-500 text-white rounded-lg py-3 text-sm font-medium transition-colors disabled:opacity-50"
          >
            {loading ? <Loader size={16} className="animate-spin" /> : <Play size={16} />}
            {loading ? "Running..." : "Run Agent"}
          </button>

          {iterations > 0 && (
            <p className="text-xs text-gray-400">
              Reflexion iterations: <span className="text-primary font-bold">{iterations}</span>
            </p>
          )}
        </div>

        <div className="col-span-2">
          <label className="text-sm text-gray-400 mb-2 block">Output</label>
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-4 text-red-400 text-sm">
              {error}
            </div>
          )}
          <div className="bg-dark border border-border rounded-lg p-4 h-96 overflow-y-auto">
            {loading ? (
              <div className="flex items-center gap-2 text-gray-400 text-sm">
                <Loader size={14} className="animate-spin" />
                Agent thinking...
              </div>
            ) : output ? (
              <pre className="text-sm text-gray-300 whitespace-pre-wrap font-mono">{output}</pre>
            ) : (
              <p className="text-gray-500 text-sm">Output will appear here...</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};