import { useState } from "react";
import ConnectionPage from "./pages/ConnectionPage";
import AnalysisProgressPage from "./pages/AnalysisProgressPage";
import ReportPage from "./pages/ReportPage";
import type { UpgradeReport } from "./types/report";

type View = "connect" | "progress" | "report";

export default function App() {
  const [view, setView] = useState<View>("connect");
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [report, setReport] = useState<UpgradeReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  function reset() {
    setView("connect");
    setAnalysisId(null);
    setReport(null);
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

        {view === "connect" && !error && (
          <ConnectionPage
            onStarted={(id) => {
              setAnalysisId(id);
              setView("progress");
            }}
          />
        )}

        {view === "progress" && analysisId && !error && (
          <AnalysisProgressPage
            analysisId={analysisId}
            onComplete={(r) => {
              setReport(r);
              setView("report");
            }}
            onError={(msg) => setError(msg)}
          />
        )}

        {view === "report" && report && <ReportPage report={report} onReset={reset} />}
      </main>
    </div>
  );
}
