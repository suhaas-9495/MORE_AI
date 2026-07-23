import React from "react";
import { NavLink } from "react-router-dom";
import {
  Bot, GitBranch, BarChart2, Shield, Database,
  Brain, Layers, LogOut, Zap
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

const nav = [
  { to: "/", icon: Zap, label: "Dashboard" },
  { to: "/agent", icon: Bot, label: "Agent Runner" },
  { to: "/pipeline", icon: GitBranch, label: "Pipeline" },
  { to: "/eval", icon: BarChart2, label: "Eval Metrics" },
  { to: "/approvals", icon: Shield, label: "Approvals" },
  { to: "/memory", icon: Brain, label: "Memory" },
  { to: "/rag", icon: Database, label: "RAG" },
  { to: "/registry", icon: Layers, label: "Registry" },
];

export const Sidebar = () => {
  const { logout, username } = useAuth();

  return (
    <div className="w-64 h-screen bg-card border-r border-border flex flex-col fixed left-0 top-0">
      <div className="p-6 border-b border-border">
        <h1 className="text-xl font-bold text-primary">MoreAI</h1>
        <p className="text-xs text-gray-400 mt-1">Multi-Agent SDLC Platform</p>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {nav.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all ${
                isActive
                  ? "bg-primary text-white"
                  : "text-gray-400 hover:bg-border hover:text-white"
              }`
            }
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-border">
        <p className="text-xs text-gray-400 mb-2">Logged in as <span className="text-white">{username}</span></p>
        <button
          onClick={logout}
          className="flex items-center gap-2 text-sm text-gray-400 hover:text-red-400 transition-colors"
        >
          <LogOut size={14} />
          Logout
        </button>
      </div>
    </div>
  );
};