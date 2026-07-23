import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { register } from "../api/client";

export const Login = () => {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isRegister, setIsRegister] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setLoading(true);
    setError("");
    try {
      if (isRegister) {
        await register(username, password);
      }
      await login(username, password);
    } catch (e: any) {
      setError(e.response?.data?.detail || "Something went wrong");
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-dark">
      <div className="bg-card border border-border rounded-2xl p-8 w-full max-w-md">
        <h1 className="text-2xl font-bold text-white mb-1">MoreAI</h1>
        <p className="text-gray-400 text-sm mb-6">Multi-Agent SDLC Platform</p>

        <div className="space-y-4">
          <input
            className="w-full bg-dark border border-border rounded-lg px-4 py-3 text-white text-sm focus:outline-none focus:border-primary"
            placeholder="Username"
            value={username}
            onChange={e => setUsername(e.target.value)}
          />
          <input
            type="password"
            className="w-full bg-dark border border-border rounded-lg px-4 py-3 text-white text-sm focus:outline-none focus:border-primary"
            placeholder="Password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleSubmit()}
          />

          {error && <p className="text-red-400 text-sm">{error}</p>}

          <button
            onClick={handleSubmit}
            disabled={loading}
            className="w-full bg-primary hover:bg-indigo-500 text-white rounded-lg py-3 text-sm font-medium transition-colors disabled:opacity-50"
          >
            {loading ? "Loading..." : isRegister ? "Register & Login" : "Login"}
          </button>

          <button
            onClick={() => setIsRegister(!isRegister)}
            className="w-full text-gray-400 text-sm hover:text-white transition-colors"
          >
            {isRegister ? "Already have an account? Login" : "No account? Register"}
          </button>
        </div>
      </div>
    </div>
  );
};