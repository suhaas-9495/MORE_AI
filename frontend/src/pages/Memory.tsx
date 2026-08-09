import React, { useState, useEffect } from "react";
import { getMemoryStats, recallMemory } from "../api/client";
import { Brain, Search, Loader } from "lucide-react";

export const Memory = () => {
  const [stats, setStats] = useState<any>(null);
  const [query, setQuery] = useState("");
  const [memories, setMemories] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getMemoryStats().then(r => setStats(r.data)).catch(() => {});
  }, []);

  const handleRecall = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const res = await recallMemory(query);
      setMemories(res.data.memories || "No relevant memories found.");
    } catch { setMemories("Failed to retrieve memories."); }
    setLoading(false);
  };

  return (
    <div className="p-8">
      <div className="flex items-center gap-3 mb-6">
        <Brain size={24} className="text-purple-400" />
        <h2 className="text-2xl font-bold text-white">Agent Memory</h2>
      </div>
      <div className="grid grid-cols-2 gap-4 mb-8">
        <div className="bg-card border border-border rounded-xl p-5">
          <p className="text-gray-400 text-sm mb-1">Total Memories Stored</p>
          <p className="text-3xl font-bold text-white">{stats?.total_memories ?? "—"}</p>
          <p className="text-xs text-gray-500 mt-1">Persisted in ChromaDB</p>
        </div>
        <div className="bg-card border border-border rounded-xl p-5">
          <p className="text-gray-400 text-sm mb-1">Memory Types</p>
          <div className="flex gap-2 mt-2">
            <span className="text-xs bg-purple-500/20 text-purple-400 border border-purple-500/30 px-2 py-1 rounded">Long-term (ChromaDB)</span>
            <span className="text-xs bg-blue-500/20 text-blue-400 border border-blue-500/30 px-2 py-1 rounded">Short-term (Session)</span>
          </div>
        </div>
      </div>
      <div className="bg-card border border-border rounded-xl p-6">
        <h3 className="text-white font-medium mb-4">Recall Memory</h3>
        <div className="flex gap-3 mb-4">
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleRecall()}
            placeholder="e.g. JWT auth system, rate limiter..."
            className="flex-1 bg-dark border border-border rounded-lg px-4 py-3 text-white text-sm focus:outline-none focus:border-purple-400"
          />
          <button
            onClick={handleRecall}
            disabled={loading || !query.trim()}
            className="flex items-center gap-2 bg-purple-500/20 hover:bg-purple-500/30 text-purple-400 border border-purple-500/30 rounded-lg px-4 py-3 text-sm transition-colors disabled:opacity-50"
          >
            {loading ? <Loader size={14} className="animate-spin" /> : <Search size={14} />}
            Recall
          </button>
        </div>
        {memories && (
          <div className="bg-dark border border-border rounded-lg p-4">
            <pre className="text-sm text-gray-300 whitespace-pre-wrap">{memories}</pre>
          </div>
        )}
      </div>
    </div>
  );
};