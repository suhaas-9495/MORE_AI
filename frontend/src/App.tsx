import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { Sidebar } from "./components/Sidebar";
import { Login } from "./pages/Login";
import { Dashboard } from "./pages/Dashboard";
import { AgentRunner } from "./pages/AgentRunner";
import { Pipeline } from "./pages/Pipeline";
import { EvalMetrics } from "./pages/EvalMetrics";
import { Approvals } from "./pages/Approvals";

const Layout = ({ children }: { children: React.ReactNode }) => (
  <div className="flex">
    <Sidebar />
    <main className="ml-64 flex-1 min-h-screen">{children}</main>
  </div>
);

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />;
};

const App = () => (
  <AuthProvider>
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/*" element={
          <ProtectedRoute>
            <Layout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/agent" element={<AgentRunner />} />
                <Route path="/pipeline" element={<Pipeline />} />
                <Route path="/eval" element={<EvalMetrics />} />
                <Route path="/approvals" element={<Approvals />} />
              </Routes>
            </Layout>
          </ProtectedRoute>
        } />
      </Routes>
    </BrowserRouter>
  </AuthProvider>
);

export default App;