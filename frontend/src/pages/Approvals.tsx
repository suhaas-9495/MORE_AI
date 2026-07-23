import React, { useState, useEffect } from "react";
import { getPendingApprovals, decideApproval } from "../api/client";
import { Shield, Check, X, RefreshCw } from "lucide-react";

export const Approvals = () => {
  const [approvals, setApprovals] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [reason, setReason] = useState("");

  const fetchApprovals = async () => {
    setLoading(true);
    try {
      const res = await getPendingApprovals();
      setApprovals(res.data);
    } catch (e) {}
    setLoading(false);
  };

  useEffect(() => {
    fetchApprovals();
    const interval = setInterval(fetchApprovals, 5000);
    return () => clearInterval(interval);
  }, []);

  const decide = async (id: string, approved: boolean) => {
    try {
      await decideApproval(id, approved, reason);
      fetchApprovals();
    } catch (e) {}
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Shield size={24} className="text-primary" />
          <h2 className="text-2xl font-bold text-white">Human Approvals</h2>
        </div>
        <button onClick={fetchApprovals} className="text-gray-400 hover:text-white">
          <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
        </button>
      </div>

      {approvals.length === 0 ? (
        <div className="bg-card border border-border rounded-xl p-12 text-center">
          <Shield size={48} className="text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400">No pending approvals</p>
          <p className="text-gray-600 text-sm mt-1">Auto-refreshing every 5 seconds</p>
        </div>
      ) : (
        <div className="space-y-4">
          {approvals.map((a: any) => (
            <div key={a.approval_id} className="bg-card border border-border rounded-xl p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <p className="text-white font-medium">{a.action_description}</p>
                  <p className="text-gray-400 text-xs mt-1">ID: {a.approval_id}</p>
                  <p className="text-gray-400 text-xs">Created: {new Date(a.created_at).toLocaleString()}</p>
                </div>
                <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-1 rounded">
                  PENDING
                </span>
              </div>

              {a.payload?.code_preview && (
                <div className="bg-dark rounded-lg p-3 mb-4">
                  <p className="text-xs text-gray-400 mb-1">Code preview:</p>
                  <pre className="text-xs text-gray-300 overflow-x-auto">{a.payload.code_preview}</pre>
                </div>
              )}

              <input
                className="w-full bg-dark border border-border rounded-lg px-3 py-2 text-white text-sm mb-3 focus:outline-none focus:border-primary"
                placeholder="Rejection reason (optional)"
                value={reason}
                onChange={e => setReason(e.target.value)}
              />

              <div className="flex gap-3">
                <button
                  onClick={() => decide(a.approval_id, true)}
                  className="flex items-center gap-2 bg-green-500/20 hover:bg-green-500/30 text-green-400 border border-green-500/30 rounded-lg px-4 py-2 text-sm transition-colors"
                >
                  <Check size={14} /> Approve
                </button>
                <button
                  onClick={() => decide(a.approval_id, false)}
                  className="flex items-center gap-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/30 rounded-lg px-4 py-2 text-sm transition-colors"
                >
                  <X size={14} /> Reject
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};