import React, { useState, useEffect } from "react";
import { getTools, getAgents } from "../api/client";
import { Layers, Wrench, Bot, ChevronDown, ChevronUp } from "lucide-react";

const ExpandableCard = ({ title, items, renderItem }: any) => {
  const [expanded, setExpanded] = useState(false);
  const visible = expanded ? items : items.slice(0, 3);
  return (
    <div className="bg-card border border-border rounded-xl p-6">
      <h3 className="text-white font-medium mb-4">{title} ({items.length})</h3>
      <div className="space-y-3">{visible.map((item: any, i: number) => renderItem(item, i))}</div>
      {items.length > 3 && (
        <button onClick={() => setExpanded(!expanded)} className="mt-3 flex items-center gap-1 text-xs text-gray-400 hover:text-white transition-colors">
          {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          {expanded ? "Show less" : `Show ${items.length - 3} more`}
        </button>
      )}
    </div>
  );
};

export const Registry = () => {
  const [tools, setTools] = useState<any[]>([]);
  const [agents, setAgents] = useState<any[]>([]);

  useEffect(() => {
    getTools().then(r => setTools(r.data)).catch(() => {});
    getAgents().then(r => setAgents(r.data)).catch(() => {});
  }, []);

  return (
    <div className="p-8">
      <div className="flex items-center gap-3 mb-6">
        <Layers size={24} className="text-yellow-400" />
        <h2 className="text-2xl font-bold text-white">Tool + Agent Registry</h2>
      </div>
      <div className="grid grid-cols-2 gap-6">
        <ExpandableCard
          title="Registered Tools" items={tools}
          renderItem={(tool: any, i: number) => (
            <div key={i} className="border border-border rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Wrench size={14} className="text-yellow-400" />
                  <span className="text-white text-sm font-medium">{tool.name}</span>
                </div>
                <span className="text-xs text-gray-400">v{tool.version}</span>
              </div>
              <p className="text-gray-400 text-xs mb-2">{tool.description}</p>
              <span className={`text-xs px-2 py-0.5 rounded-full ${tool.enabled ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"}`}>
                {tool.enabled ? "enabled" : "disabled"}
              </span>
            </div>
          )}
        />
        <ExpandableCard
          title="Registered Agents" items={agents}
          renderItem={(agent: any, i: number) => (
            <div key={i} className="border border-border rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Bot size={14} className="text-primary" />
                  <span className="text-white text-sm font-medium">{agent.name}</span>
                </div>
                <span className="text-xs bg-primary/20 text-primary px-2 py-0.5 rounded">v{agent.version}</span>
              </div>
              <p className="text-gray-400 text-xs mb-3">{agent.description}</p>
              <div className="flex flex-wrap gap-1">
                {agent.capabilities?.map((cap: string) => (
                  <span key={cap} className="text-xs bg-dark border border-border px-2 py-0.5 rounded text-gray-300">{cap}</span>
                ))}
              </div>
            </div>
          )}
        />
      </div>
    </div>
  );
};