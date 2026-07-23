import React, { useState, useEffect } from "react";
import { getEvalMetrics, runRegressionV2 } from "../api/client";
import { BarChart2, Play, Loader, TrendingUp } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

export const EvalMetrics = () => {
  const [metrics, setMetrics] = useState<any>(null);
  const [running, setRunning] = useState(false);
  const [regressionResult, setRegressionResult] = useState<any>(null);

  useEffect(() => {
    getEvalMetrics().then(r => setMetrics(r.data)).catch(() => {});
  }, []);

  const runRegression = async () => {
    setRunning(true);
    try {
      const res = await runRegressionV2();
      setRegressionResult(res.data);
      getEvalMetrics().then(r => setMetrics(r.data)).catch(() => {});
    } catch (e) {}
    setRunning(false);
  };

  const agentData = metrics?.by_agent_type
    ? Object.entries(metrics.by_agent_type).map(([agent, data]: any) => ({
        agent,
        passed: data.passed,
        total: data.total,
        rate: data.total > 0 ? Math.round((data.passed / data.total) * 100) : 0,
      }))
    : [];

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <BarChart2 size={24} className="text-primary" />
          <h2 className="text-2xl font-bold text-white">Eval Metrics</h2>
        </div>
        <button
          onClick={runRegression}
          disabled={running}
          className="flex items-center gap-2 bg-primary hover:bg-indigo-500 text-white rounded-lg px-4 py-2 text-sm transition-colors disabled:opacity-50"
        >
          {running ? <Loader size={14} className="animate-spin" /> : <Play size={14} />}
          Run Regression Suite
        </button>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-8">
        {[
          ["Total Runs", metrics?.total_runs ?? "—"],
          ["Success Rate", metrics ? `${(metrics.success_rate * 100).toFixed(1)}%` : "—"],
          ["Avg Judge Score", metrics?.avg_judge_score ?? "—"],
          ["Total Cost", metrics ? `$${metrics.total_cost_usd}` : "—"],
        ].map(([label, value]) => (
          <div key={label} className="bg-card border border-border rounded-xl p-5">
            <p className="text-gray-400 text-sm mb-1">{label}</p>
            <p className="text-2xl font-bold text-white">{value}</p>
          </div>
        ))}
      </div>

      {agentData.length > 0 && (
        <div className="bg-card border border-border rounded-xl p-6 mb-6">
          <h3 className="text-white font-medium mb-4 flex items-center gap-2">
            <TrendingUp size={16} className="text-primary" />
            Success Rate by Agent
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={agentData}>
              <XAxis dataKey="agent" tick={{ fill: "#9ca3af", fontSize: 12 }} />
              <YAxis tick={{ fill: "#9ca3af", fontSize: 12 }} domain={[0, 100]} />
              <Tooltip
                contentStyle={{ backgroundColor: "#1a1a2e", border: "1px solid #2a2a4a", borderRadius: 8 }}
                labelStyle={{ color: "#fff" }}
              />
              <Bar dataKey="rate" radius={[4, 4, 0, 0]}>
                {agentData.map((_, i) => (
                  <Cell key={i} fill={_ .rate >= 70 ? "#22c55e" : "#ef4444"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {regressionResult && (
        <div className={`border rounded-xl p-6 ${regressionResult.ci_passed ? "bg-green-500/10 border-green-500/30" : "bg-red-500/10 border-red-500/30"}`}>
          <h3 className={`font-medium mb-3 ${regressionResult.ci_passed ? "text-green-400" : "text-red-400"}`}>
            Regression Suite {regressionResult.ci_passed ? "✅ PASSED" : "❌ FAILED"}
          </h3>
          <div className="grid grid-cols-3 gap-4 text-sm">
            {[
              ["Success Rate", regressionResult.success_rate],
              ["P50 Latency", `${regressionResult.p50_latency_s}s`],
              ["P95 Latency", `${regressionResult.p95_latency_s}s`],
            ].map(([k, v]) => (
              <div key={k}>
                <p className="text-gray-400">{k}</p>
                <p className="text-white font-medium">{v}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};