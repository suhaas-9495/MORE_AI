import React, { useState } from "react";
import { runPipeline } from "../api/client";
import { GitBranch, Play, Loader, CheckCircle, Clock } from "lucide-react";

const STAGES = ["Research", "Plan", "Code", "Test", "Review", "Human Gate", "Document", "Deploy"];

export const Pipeline = () => {
  const [task, setTask] = useState("");
  const [requireApproval, setRequireApproval] = useState(true);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");

  const handleRun = async () => {
    if (!task.trim()) return;
    setLoading(true);
    setResult(null);
    setError("");
    try {
      const res = await runPipeline(task, requireApproval);
      setResult(res.data);
    } catch (e: any) {
      setError(e.response?.data?.detail || "Pipeline failed");
    }
    setLoading(false);
  };

  return (
    <div className="p-8">
      <div className="flex items-center gap-3 mb-6">
        <GitBranch size={24} className="text-primary" />
        <h2 className="text-2xl font-bold text-white">SDLC Pipeline</h2>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-1 space-y-4">
          <div>
            <label className="text-sm text-gray-400 mb-2 block">Task / Requirement</label>
            <textarea
              value={task}
              onChange={e => setTask(e.target.value)}
              placeholder="Describe what you want to build..."
              rows={6}
              className="w-full bg-dark border border-border rounded-lg px-4 py-3 text-white text-sm focus:outline-none focus:border-primary resize-none"
            />
          </div>

          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={requireApproval}
              onChange={e => setRequireApproval(e.target.checked)}
              className="accent-primary w-4 h-4"
            />
            <span className="text-sm text-gray-300">Require human approval before deploy</span>
          </label>

          <button
            onClick={handleRun}
            disabled={loading || !task.trim()}
            className="w-full flex items-center justify-center gap-2 bg-primary hover:bg-indigo-500 text-white rounded-lg py-3 text-sm font-medium transition-colors disabled:opacity-50"
          >
            {loading ? <Loader size={16} className="animate-spin" /> : <Play size={16} />}
            {loading ? "Pipeline Running..." : "Start Pipeline"}
          </button>
        </div>

        <div className="col-span-2">
          <div className="bg-card border border-border rounded-xl p-6 mb-4">
            <h3 className="text-white font-medium mb-4">Pipeline Stages</h3>
            <div className="flex flex-wrap gap-2">
              {STAGES.map((stage, i) => (
                <div key={stage} className="flex items-center gap-2">
                  <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium ${
                    stage === "Human Gate"
                      ? "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30"
                      : "bg-primary/20 text-primary border border-primary/30"
                  }`}>
                    {loading ? <Loader size={10} className="animate-spin" /> : <CheckCircle size={10} />}
                    {stage}
                  </div>
                  {i < STAGES.length - 1 && <span className="text-gray-600">→</span>}
                </div>
              ))}
            </div>
          </div>

          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-400 text-sm mb-4">
              {error}
            </div>
          )}

          {result && (
            <div className="bg-card border border-border rounded-xl p-6">
              <div className="flex items-center gap-2 mb-4">
                <CheckCircle size={16} className="text-green-400" />
                <span className="text-white font-medium">Pipeline {result.status}</span>
                {result.state_id && (
                  <span className="text-xs text-gray-400 ml-auto">ID: {result.state_id}</span>
                )}
              </div>
              {result.status === "awaiting_approval" || result.approval_id ? (
                <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                  <p className="text-yellow-400 text-sm flex items-center gap-2">
                    <Clock size={14} />
                    Waiting for approval. Go to the Approvals tab to approve or reject.
                  </p>
                  <p className="text-gray-400 text-xs mt-1">Approval ID: {result.approval_id}</p>
                </div>
              ) : (
                <p className="text-green-400 text-sm">Pipeline completed successfully.</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};