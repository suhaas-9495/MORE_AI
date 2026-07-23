import React, { useEffect, useState } from "react";
import { getEvalMetrics, getMemoryStats, getTools, getAgents } from "../api/client";
import { BarChart2, Brain, Layers, Zap } from "lucide-react";

const StatCard = ({ label, value, icon: Icon, color }: any) => (
  <div className="bg-card border border-border rounded-xl p-5">
    <div className="flex items-center justify-between mb-3">
      <span className="text-gray-400 text-sm">{label}</span>
      <Icon size={18} className={color} />
    </div>
    <p className="text-2xl font-bold text-white">{value ?? "—"}</p>
  </div>
);

export const Dashboard = () => {
  const [metrics, setMetrics] = useState<any>(null);
  const [memory, setMemory] = useState<any>(null);
  const [tools, setTools] = useState<any[]>([]);
  const [agents, setAgents] = useState<any[]>([]);

  useEffect(() => {
    getEvalMetrics().then(r => setMetrics(r.data)).catch(() => {});
    getMemoryStats().then(r => setMemory(r.data)).catch(() => {});
    getTools().then(r => setTools(r.data)).catch(() => {});
    getAgents().then(r => setAgents(r.data)).catch(() => {});
  }, []);

  return (
    <div className="p-8">
      <h2 className="text-2xl font-bold text-white mb-2">Dashboard</h2>
      <p className="text-gray-400 text-sm mb-8">MoreAI Multi-Agent SDLC Platform</p>

      <div className="grid grid-cols-2 gap-4 mb-8 lg:grid-cols-4">
        <StatCard label="Success Rate" value={metrics ? `${(metrics.success_rate * 100).toFixed(1)}%` : null} icon={BarChart2} color="text-green-400" />
        <StatCard label="Total Runs" value={metrics?.total_runs} icon={Zap} color="text-primary" />
        <StatCard label="Memories Stored" value={memory?.total_memories} icon={Brain} color="text-purple-400" />
        <StatCard label="Tools Registered" value={tools.length} icon={Layers} color="text-yellow-400" />
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="bg-card border border-border rounded-xl p-5">
          <h3 className="text-white font-medium mb-4">Registered Agents</h3>
          <div className="space-y-2">
            {agents.map((a: any) => (
              <div key={a.agent_id} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                <span className="text-sm text-white">{a.name}</span>
                <span className="text-xs text-primary bg-primary/10 px-2 py-1 rounded">{a.version}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-card border border-border rounded-xl p-5">
          <h3 className="text-white font-medium mb-4">Eval Overview</h3>
          {metrics ? (
            <div className="space-y-3">
              {[
                ["Total Runs", metrics.total_runs],
                ["Passed", metrics.passed],
                ["Avg Judge Score", metrics.avg_judge_score],
                ["Total Cost", `$${metrics.total_cost_usd}`],
              ].map(([k, v]) => (
                <div key={k} className="flex justify-between text-sm">
                  <span className="text-gray-400">{k}</span>
                  <span className="text-white font-medium">{v}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">No eval data yet. Run /eval/metrics.</p>
          )}
        </div>
      </div>
    </div>
  );
};