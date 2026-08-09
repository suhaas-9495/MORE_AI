import React, { useState } from "react";
import { ingestDocument, retrieveContext } from "../api/client";
import { Database, Upload, Search, Loader, CheckCircle } from "lucide-react";

export const RAG = () => {
  const [ingestText, setIngestText] = useState("");
  const [source, setSource] = useState("");
  const [ingestLoading, setIngestLoading] = useState(false);
  const [ingestResult, setIngestResult] = useState<any>(null);
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(5);
  const [retrieveLoading, setRetrieveLoading] = useState(false);
  const [context, setContext] = useState("");

  const handleIngest = async () => {
    if (!ingestText.trim()) return;
    setIngestLoading(true);
    setIngestResult(null);
    try {
      const res = await ingestDocument(ingestText, source || "manual");
      setIngestResult(res.data);
    } catch (e: any) {
      setIngestResult({ status: "error", detail: e.response?.data?.detail });
    }
    setIngestLoading(false);
  };

  const handleRetrieve = async () => {
    if (!query.trim()) return;
    setRetrieveLoading(true);
    setContext("");
    try {
      const res = await retrieveContext(query, topK);
      setContext(res.data.context || "No relevant context found.");
    } catch { setContext("Retrieval failed."); }
    setRetrieveLoading(false);
  };

  return (
    <div className="p-8">
      <div className="flex items-center gap-3 mb-6">
        <Database size={24} className="text-teal-400" />
        <h2 className="text-2xl font-bold text-white">RAG — Knowledge Base</h2>
      </div>
      <div className="grid grid-cols-2 gap-6">
        <div className="bg-card border border-border rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <Upload size={16} className="text-teal-400" />
            <h3 className="text-white font-medium">Ingest Document</h3>
          </div>
          <input
            value={source}
            onChange={e => setSource(e.target.value)}
            placeholder="Source label (e.g. 'fastapi_docs')"
            className="w-full bg-dark border border-border rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:border-teal-400 mb-3"
          />
          <textarea
            value={ingestText}
            onChange={e => setIngestText(e.target.value)}
            placeholder="Paste document text here..."
            rows={8}
            className="w-full bg-dark border border-border rounded-lg px-4 py-3 text-white text-sm focus:outline-none focus:border-teal-400 resize-none mb-3"
          />
          <button
            onClick={handleIngest}
            disabled={ingestLoading || !ingestText.trim()}
            className="w-full flex items-center justify-center gap-2 bg-teal-500/20 hover:bg-teal-500/30 text-teal-400 border border-teal-500/30 rounded-lg py-2.5 text-sm transition-colors disabled:opacity-50"
          >
            {ingestLoading ? <Loader size={14} className="animate-spin" /> : <Upload size={14} />}
            {ingestLoading ? "Ingesting..." : "Ingest Document"}
          </button>
          {ingestResult && (
            <div className={`mt-3 p-3 rounded-lg text-sm flex items-center gap-2 ${ingestResult.status === "success" ? "bg-green-500/10 border border-green-500/30 text-green-400" : "bg-red-500/10 border border-red-500/30 text-red-400"}`}>
              {ingestResult.status === "success" && <CheckCircle size={14} />}
              {ingestResult.status === "success" ? `✅ Stored ${ingestResult.chunks_stored} chunks from "${ingestResult.source}"` : `Error: ${ingestResult.detail}`}
            </div>
          )}
        </div>
        <div className="bg-card border border-border rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <Search size={16} className="text-teal-400" />
            <h3 className="text-white font-medium">Retrieve Context</h3>
          </div>
          <p className="text-gray-400 text-xs mb-4">Hybrid search (BM25 + semantic) across your knowledge base.</p>
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleRetrieve()}
            placeholder="What do you want to find?"
            className="w-full bg-dark border border-border rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:border-teal-400 mb-3"
          />
          <div className="flex items-center gap-3 mb-3">
            <label className="text-gray-400 text-sm">Top-K:</label>
            <input
              type="number" value={topK}
              onChange={e => setTopK(Number(e.target.value))}
              min={1} max={20}
              className="w-20 bg-dark border border-border rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-teal-400"
            />
          </div>
          <button
            onClick={handleRetrieve}
            disabled={retrieveLoading || !query.trim()}
            className="w-full flex items-center justify-center gap-2 bg-teal-500/20 hover:bg-teal-500/30 text-teal-400 border border-teal-500/30 rounded-lg py-2.5 text-sm transition-colors disabled:opacity-50"
          >
            {retrieveLoading ? <Loader size={14} className="animate-spin" /> : <Search size={14} />}
            {retrieveLoading ? "Searching..." : "Retrieve"}
          </button>
          {context && (
            <div className="mt-3 bg-dark border border-border rounded-lg p-4 max-h-64 overflow-y-auto">
              <pre className="text-xs text-gray-300 whitespace-pre-wrap">{context}</pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
