import { useState } from "react";
import ConnectionPage from "./pages/ConnectionPage";
import AnalysisProgressPage from "./pages/AnalysisProgressPage";
import ReportPage from "./pages/ReportPage";
import AgentGoalPage from "./pages/AgentGoalPage";
import AgentRunPage from "./pages/AgentRunPage";
import AgentReportPage from "./pages/AgentReportPage";
import type { UpgradeReport } from "./types/report";
import type { AgentReport } from "./types/agent";

type Mode = "workflow" | "agent";
type View = "connect" | "progress" | "report" | "agent-goal" | "agent-run" | "agent-report";

export default function App() {
  const [mode, setMode] = useState<Mode>("workflow");
  const [view, setView] = useState<View>("connect");
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [report, setReport] = useState<UpgradeReport | null>(null);
  const [runId, setRunId] = useState<string | null>(null);
  const [agentReport, setAgentReport] = useState<AgentReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  function reset() {
    setView(mode === "agent" ? "agent-goal" : "connect");
    setAnalysisId(null);
    setReport(null);
    setRunId(null);
    setAgentReport(null);
    setError(null);
  }

  function switchMode(next: Mode) {
    setMode(next);
    setView(next === "agent" ? "agent-goal" : "connect");
    setAnalysisId(null);
    setReport(null);
    setRunId(null);
    setAgentReport(null);
    setError(null);
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-5xl px-6 py-4">
          <h1 className="text-xl font-bold text-slate-900">Kubernetes Upgrade Assistant</h1>
          <p className="text-sm text-slate-500">
            클러스터를 분석해 안전한 Kubernetes Upgrade Plan을 자동으로 생성합니다.
          </p>
          <div className="mt-4 flex gap-2">
            <button
              onClick={() => switchMode("workflow")}
              className={`rounded-md px-3 py-1.5 text-sm font-medium ${
                mode === "workflow" ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              클러스터 분석
            </button>
            <button
              onClick={() => switchMode("agent")}
              className={`rounded-md px-3 py-1.5 text-sm font-medium ${
                mode === "agent" ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              자율 에이전트
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-8">
        {error && (
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {error}
            <button onClick={reset} className="ml-3 underline">
              다시 시도
            </button>
          </div>
        )}

        {mode === "workflow" && view === "connect" && !error && (
          <ConnectionPage
            onStarted={(id) => {
              setAnalysisId(id);
              setView("progress");
            }}
          />
        )}

        {mode === "workflow" && view === "progress" && analysisId && !error && (
          <AnalysisProgressPage
            analysisId={analysisId}
            onComplete={(r) => {
              setReport(r);
              setView("report");
            }}
            onError={(msg) => setError(msg)}
          />
        )}

        {mode === "workflow" && view === "report" && report && <ReportPage report={report} onReset={reset} />}

        {mode === "agent" && view === "agent-goal" && !error && (
          <AgentGoalPage
            onStarted={(id) => {
              setRunId(id);
              setView("agent-run");
            }}
          />
        )}

        {mode === "agent" && view === "agent-run" && runId && !error && (
          <AgentRunPage
            runId={runId}
            onComplete={(r) => {
              setAgentReport(r);
              setView("agent-report");
            }}
            onError={(msg) => setError(msg)}
          />
        )}

        {mode === "agent" && view === "agent-report" && agentReport && (
          <AgentReportPage report={agentReport} onReset={reset} />
        )}
      </main>
    </div>
  );
}
