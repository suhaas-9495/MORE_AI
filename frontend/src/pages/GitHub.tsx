import React, { useState } from "react";
import axios from "axios";
import { GitBranch, Search, MessageSquare, Loader, CheckCircle, FileText } from "lucide-react";

const api = axios.create({ baseURL: "http://localhost:8000" });
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const GitHub = () => {
  const [repoName, setRepoName] = useState("suhaas-9495/MORE_AI");
  const [prNumber, setPrNumber] = useState("");
  const [postComment, setPostComment] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");
  const [openPRs, setOpenPRs] = useState<any[]>([]);
  const [loadingPRs, setLoadingPRs] = useState(false);
  const [activeTab, setActiveTab] = useState<"review" | "prs">("review");

  const handleReview = async () => {
    if (!repoName || !prNumber) return;
    setLoading(true);
    setResult(null);
    setError("");
    try {
      const res = await api.post("/github/pr/review", {
        repo_name: repoName,
        pr_number: parseInt(prNumber),
        post_comment: postComment,
      });
      setResult(res.data);
    } catch (e: any) {
      setError(e.response?.data?.detail || "Review failed");
    }
    setLoading(false);
  };

  const loadOpenPRs = async () => {
    if (!repoName) return;
    setLoadingPRs(true);
    try {
      const [owner, repo] = repoName.split("/");
      const res = await api.get(`/github/repo/${owner}/${repo}/prs`);
      setOpenPRs(res.data);
    } catch (e: any) {
      setError(e.response?.data?.detail || "Failed to load PRs");
    }
    setLoadingPRs(false);
  };

  return (
    <div className="p-8">
      <div className="flex items-center gap-3 mb-6">
        <GitBranch size={24} className="text-white" />
        <h2 className="text-2xl font-bold text-white">GitHub Integration</h2>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {(["review", "prs"] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === tab
                ? "bg-primary text-white"
                : "bg-card border border-border text-gray-400 hover:text-white"
            }`}
          >
            {tab === "review" ? "PR Review" : "Open PRs"}
          </button>
        ))}
      </div>

      {/* Repo input */}
      <div className="bg-card border border-border rounded-xl p-6 mb-6">
        <label className="text-sm text-gray-400 mb-2 block">Repository</label>
        <input
          value={repoName}
          onChange={e => setRepoName(e.target.value)}
          placeholder="owner/repo (e.g. suhaas-9495/MORE_AI)"
          className="w-full bg-dark border border-border rounded-lg px-4 py-3 text-white text-sm focus:outline-none focus:border-primary mb-3"
        />

        {activeTab === "review" && (
          <>
            <label className="text-sm text-gray-400 mb-2 block">PR Number</label>
            <input
              value={prNumber}
              onChange={e => setPrNumber(e.target.value)}
              placeholder="e.g. 42"
              type="number"
              className="w-full bg-dark border border-border rounded-lg px-4 py-3 text-white text-sm focus:outline-none focus:border-primary mb-3"
            />
            <label className="flex items-center gap-3 mb-4 cursor-pointer">
              <input
                type="checkbox"
                checked={postComment}
                onChange={e => setPostComment(e.target.checked)}
                className="accent-primary w-4 h-4"
              />
              <span className="text-sm text-gray-300">
                Post review as GitHub PR comment
              </span>
            </label>
            <button
              onClick={handleReview}
              disabled={loading || !repoName || !prNumber}
              className="flex items-center gap-2 bg-primary hover:bg-indigo-500 text-white rounded-lg px-6 py-2.5 text-sm transition-colors disabled:opacity-50"
            >
              {loading
                ? <Loader size={14} className="animate-spin" />
                : <MessageSquare size={14} />}
              {loading ? "Reviewing..." : "Review PR"}
            </button>
          </>
        )}

        {activeTab === "prs" && (
          <button
            onClick={loadOpenPRs}
            disabled={loadingPRs}
            className="flex items-center gap-2 bg-primary hover:bg-indigo-500 text-white rounded-lg px-6 py-2.5 text-sm transition-colors disabled:opacity-50"
          >
            {loadingPRs
              ? <Loader size={14} className="animate-spin" />
              : <Search size={14} />}
            Load Open PRs
          </button>
        )}
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-4 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* PR Review Result */}
      {result && activeTab === "review" && (
        <div className="bg-card border border-border rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <CheckCircle size={16} className="text-green-400" />
            <span className="text-white font-medium">
              Review complete — {result.files_reviewed} files reviewed
            </span>
            {result.comment_posted && (
              <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded ml-auto">
                Posted to GitHub
              </span>
            )}
          </div>
          <div className="bg-dark border border-border rounded-lg p-4 max-h-96 overflow-y-auto">
            <pre className="text-sm text-gray-300 whitespace-pre-wrap">
              {result.review}
            </pre>
          </div>
        </div>
      )}

      {/* Open PRs list */}
      {openPRs.length > 0 && activeTab === "prs" && (
        <div className="bg-card border border-border rounded-xl p-6">
          <h3 className="text-white font-medium mb-4">
            Open PRs ({openPRs.length})
          </h3>
          <div className="space-y-3">
            {openPRs.map((pr: any) => (
              <div key={pr.number} className="border border-border rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-xs text-gray-400 mr-2">#{pr.number}</span>
                    <span className="text-white text-sm">{pr.title}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-gray-400">
                      {pr.files_changed} files
                    </span>
                    <button
                      onClick={() => {
                        setPrNumber(String(pr.number));
                        setActiveTab("review");
                      }}
                      className="text-xs bg-primary/20 text-primary px-2 py-1 rounded hover:bg-primary/30 transition-colors"
                    >
                      Review
                    </button>
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  by {pr.author} · {new Date(pr.created_at).toLocaleDateString()}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};