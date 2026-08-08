import React, { useState, useEffect } from "react";
import { getAllExperiments, getAgentExperiment } from "../api/client";
import { FlaskConical, TrendingUp, DollarSign, Clock, Loader } from "lucide-react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid
} from "recharts";

const AGENT_TYPES = ["planner", "coder", "reviewer", "tester", "researcher", "documenter"];

const MetricCard = ({ label, value, icon: Icon, color }: any) => (
  <div className="bg-dark border border-border rounded-lg p-4">
    <div className="flex items-center justify-between mb-2">
      <span className="text-gray-400 text-xs">{label}</span>
      <Icon size={14} className={color} />
    </div>
    <p className="text-xl font-bold text-white">{value ?? "—"}</p>
  </div>
);

export const Experiments = () => {
  const [experiments, setExperiments] = useState<any>({});
  const [selected, setSelected] = useState("coder");
  const [detail, setDetail] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getAllExperiments()
      .then(r => setExperiments(r.data))
      .catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    getAgentExperiment(selected)
      .then(r => setDetail(r.data))
      .catch(() => setDetail(null))
      .finally(() => setLoading(false));
  }, [selected]);

  const recentRuns = detail?.recent_runs?.map((r: any, i: number) => ({
    run: `Run ${i + 1}`,
    latency: r["metrics.latency_s"] ?? 0,
    score: r["metrics.judge_score"] ?? 0,
    passed: r["metrics.passed"] ?? 0,
  })) || [];

  return (
    <div className="p-8">
      <div className="flex items-center gap-3 mb-6">
        <FlaskConical size={24} className="text-green-400" />
        <h2 className="text-2xl font-bold text-white">MLflow Experiments</h2>
      </div>

      {/* Agent selector */}
      <div className="flex gap-2 mb-6 flex-wrap">
        {AGENT_TYPES.map(agent => (
          <button
            key={agent}
            onClick={() => setSelected(agent)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              selected === agent
                ? "bg-green-500/20 text-green-400 border border-green-500/30"
                : "bg-card border border-border text-gray-400 hover:text-white"
            }`}
          >
            {agent}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center gap-2 text-gray-400">
          <Loader size={16} className="animate-spin" />
          Loading experiment data...
        </div>
      ) : detail ? (
        <>
          <div className="grid grid-cols-4 gap-4 mb-6">
            <MetricCard
              label="Total Runs"
              value={detail.total_runs}
              icon={FlaskConical}
              color="text-green-400"
            />
            <MetricCard
              label="Best Judge Score"
              value={detail.best_judge_score?.toFixed(3)}
              icon={TrendingUp}
              color="text-primary"
            />
            <MetricCard
              label="Avg Latency"
              value={detail.avg_latency_s ? `${detail.avg_latency_s.toFixed(2)}s` : null}
              icon={Clock}
              color="text-yellow-400"
            />
            <MetricCard
              label="Avg Cost"
              value={detail.avg_cost_usd ? `$${detail.avg_cost_usd.toFixed(6)}` : null}
              icon={DollarSign}
              color="text-red-400"
            />
          </div>

          {recentRuns.length > 0 && (
            <div className="bg-card border border-border rounded-xl p-6 mb-6">
              <h3 className="text-white font-medium mb-4">
                Recent Runs — {selected} agent
              </h3>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={recentRuns}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2a2a4a" />
                  <XAxis dataKey="run" tick={{ fill: "#9ca3af", fontSize: 11 }} />
                  <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1a1a2e",
                      border: "1px solid #2a2a4a",
                      borderRadius: 8,
                    }}
                    labelStyle={{ color: "#fff" }}
                  />
                  <Line
                    type="monotone" dataKey="latency"
                    stroke="#6366f1" strokeWidth={2} dot={{ r: 3 }}
                    name="Latency (s)"
                  />
                  <Line
                    type="monotone" dataKey="score"
                    stroke="#22c55e" strokeWidth={2} dot={{ r: 3 }}
                    name="Judge Score"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* All agent summary */}
          <div className="bg-card border border-border rounded-xl p-6">
            <h3 className="text-white font-medium mb-4">All Agents Overview</h3>
            <div className="space-y-3">
              {Object.entries(experiments).map(([agent, data]: any) => (
                <div
                  key={agent}
                  onClick={() => setSelected(agent)}
                  className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors ${
                    selected === agent
                      ? "bg-green-500/10 border border-green-500/30"
                      : "border border-border hover:border-gray-500"
                  }`}
                >
                  <span className="text-white text-sm capitalize">{agent}</span>
                  <div className="flex gap-6 text-xs text-gray-400">
                    <span>Runs: {data.total_runs ?? "—"}</span>
                    <span>Best: {data.best_judge_score?.toFixed(2) ?? "—"}</span>
                    <span>
                      Avg: {data.avg_latency_s
                        ? `${data.avg_latency_s.toFixed(1)}s`
                        : "—"}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      ) : (
        <div className="bg-card border border-border rounded-xl p-12 text-center">
          <FlaskConical size={48} className="text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400">No experiment data yet.</p>
          <p className="text-gray-500 text-sm mt-1">
            Run agents to start collecting experiment metrics in MLflow.
          </p>
        </div>
      )}
    </div>
  );
};