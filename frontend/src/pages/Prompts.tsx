import React, { useState, useEffect } from "react";
import {
  listPrompts, getPrompt, getPromptChangelog, reloadPrompt
} from "../api/client";
import { FileText, RefreshCw, Clock, ChevronDown, ChevronUp, Loader } from "lucide-react";

const AGENT_TYPES = ["planner", "coder", "reviewer", "tester", "researcher", "documenter"];

export const Prompts = () => {
  const [prompts, setPrompts] = useState<any[]>([]);
  const [selected, setSelected] = useState("planner");
  const [detail, setDetail] = useState<any>(null);
  const [changelog, setChangelog] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [reloading, setReloading] = useState(false);
  const [showPrompt, setShowPrompt] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    listPrompts().then(r => setPrompts(r.data)).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    Promise.all([getPrompt(selected), getPromptChangelog(selected)])
      .then(([promptRes, changelogRes]) => {
        setDetail(promptRes.data);
        setChangelog(changelogRes.data.changelog || []);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [selected]);

  const handleReload = async () => {
    setReloading(true);
    try {
      const res = await reloadPrompt(selected);
      setMessage(`✅ Reloaded ${selected} v${res.data.version}`);
      setTimeout(() => setMessage(""), 3000);
    } catch (e) {
      setMessage("❌ Reload failed");
    }
    setReloading(false);
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <FileText size={24} className="text-orange-400" />
          <h2 className="text-2xl font-bold text-white">Prompt Management</h2>
        </div>
        <button
          onClick={handleReload}
          disabled={reloading}
          className="flex items-center gap-2 bg-orange-500/20 hover:bg-orange-500/30 text-orange-400 border border-orange-500/30 rounded-lg px-4 py-2 text-sm transition-colors disabled:opacity-50"
        >
          <RefreshCw size={14} className={reloading ? "animate-spin" : ""} />
          Hot Reload
        </button>
      </div>

      {message && (
        <div className="mb-4 p-3 bg-green-500/10 border border-green-500/30 rounded-lg text-green-400 text-sm">
          {message}
        </div>
      )}

      {/* Prompt version summary */}
      <div className="grid grid-cols-3 gap-3 mb-6">
        {prompts.map((p: any) => (
          <div
            key={p.agent_type}
            onClick={() => setSelected(p.agent_type)}
            className={`p-4 rounded-xl cursor-pointer transition-colors border ${
              selected === p.agent_type
                ? "bg-orange-500/10 border-orange-500/30"
                : "bg-card border-border hover:border-gray-500"
            }`}
          >
            <p className="text-white font-medium capitalize">{p.agent_type}</p>
            <p className="text-xs text-gray-400 mt-1">
              v{p.version} · {p.changelog_entries} changes
            </p>
          </div>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center gap-2 text-gray-400">
          <Loader size={16} className="animate-spin" /> Loading...
        </div>
      ) : detail ? (
        <div className="grid grid-cols-2 gap-6">
          {/* Prompt detail */}
          <div className="bg-card border border-border rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-white font-medium capitalize">{selected} Prompt</h3>
              <span className="text-xs bg-primary/20 text-primary px-2 py-1 rounded">
                v{detail.version}
              </span>
            </div>

            <div className="space-y-3 text-sm mb-4">
              <div className="flex justify-between">
                <span className="text-gray-400">Description</span>
                <span className="text-white text-right max-w-48">{detail.description}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Last modified</span>
                <span className="text-white">{detail.last_modified}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Min judge score</span>
                <span className="text-white">
                  {detail.eval_criteria?.min_judge_score}
                </span>
              </div>
            </div>

            <button
              onClick={() => setShowPrompt(!showPrompt)}
              className="flex items-center gap-2 text-sm text-gray-400 hover:text-white mb-3 transition-colors"
            >
              {showPrompt
                ? <ChevronUp size={14} />
                : <ChevronDown size={14} />}
              {showPrompt ? "Hide" : "Show"} system prompt
            </button>

            {showPrompt && (
              <div className="bg-dark border border-border rounded-lg p-4 max-h-48 overflow-y-auto">
                <pre className="text-xs text-gray-300 whitespace-pre-wrap">
                  {detail.system_prompt}
                </pre>
              </div>
            )}

            {detail.eval_criteria && (
              <div className="mt-4">
                <p className="text-gray-400 text-xs mb-2">Eval criteria keywords:</p>
                <div className="flex flex-wrap gap-1">
                  {detail.eval_criteria.expected_keywords?.map((kw: string) => (
                    <span
                      key={kw}
                      className="text-xs bg-dark border border-border px-2 py-0.5 rounded text-gray-300"
                    >
                      {kw}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Changelog */}
          <div className="bg-card border border-border rounded-xl p-6">
            <div className="flex items-center gap-2 mb-4">
              <Clock size={16} className="text-orange-400" />
              <h3 className="text-white font-medium">Changelog</h3>
            </div>

            {changelog.length === 0 ? (
              <p className="text-gray-500 text-sm">No changelog entries.</p>
            ) : (
              <div className="space-y-3">
                {[...changelog].reverse().map((entry: any, i: number) => (
                  <div
                    key={i}
                    className={`p-3 rounded-lg border ${
                      i === 0
                        ? "border-orange-500/30 bg-orange-500/5"
                        : "border-border"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-white text-sm font-medium">
                        v{entry.version}
                      </span>
                      <div className="flex items-center gap-2">
                        {entry.eval_score && (
                          <span className="text-xs text-green-400">
                            score: {entry.eval_score}
                          </span>
                        )}
                        <span className="text-xs text-gray-500">{entry.date}</span>
                      </div>
                    </div>
                    <p className="text-gray-400 text-xs">{entry.change}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
};