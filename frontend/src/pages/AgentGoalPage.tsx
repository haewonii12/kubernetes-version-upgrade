import { useEffect, useState } from "react";
import { createAgentGoal } from "../api/agentClient";
import { listTargetVersions } from "../api/client";

interface Props {
  onStarted: (runId: string) => void;
}

export default function AgentGoalPage({ onStarted }: Props) {
  const [request, setRequest] = useState("");
  const [mockMode, setMockMode] = useState(true);
  const [targetVersions, setTargetVersions] = useState<string[]>([]);
  const [targetVersion, setTargetVersion] = useState("");
  const [kubeconfig, setKubeconfig] = useState<File | null>(null);
  const [llmEndpoint, setLlmEndpoint] = useState("");
  const [llmModel, setLlmModel] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listTargetVersions()
      .then((versions) => setTargetVersions(versions))
      .catch(() => {
        // 목표 버전 없이도(현황 파악만 하는 목표) 진행 가능하므로 실패해도 무시.
      });
  }, []);

  async function handleSubmit() {
    setError(null);
    if (!request.trim()) {
      setError("무엇을 분석/판단해야 하는지 자연어로 입력해주세요.");
      return;
    }
    if (!mockMode && !kubeconfig) {
      setError("실제 클러스터 분석을 하려면 kubeconfig 파일을 업로드해야 합니다.");
      return;
    }
    setSubmitting(true);
    try {
      const runId = await createAgentGoal(request.trim(), targetVersion, mockMode, kubeconfig, {
        llmEndpoint: llmEndpoint.trim() || undefined,
        llmModel: llmModel.trim() || undefined,
      });
      onStarted(runId);
    } catch (e) {
      setError(e instanceof Error ? e.message : "실행 시작에 실패했습니다.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-xl">
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">목표 입력</h2>
        <p className="mt-1 text-sm text-slate-500">
          고정된 절차 없이, 목표를 자연어로 입력하면 에이전트가 스스로 필요한 조사를
          계획하고 실행합니다. 목표 범위를 벗어난 작업(예: 업그레이드 실행)은 절대
          자동으로 수행하지 않습니다.
        </p>

        <div className="mt-6 space-y-5">
          <div>
            <label className="block text-sm font-medium text-slate-700">목표</label>
            <textarea
              value={request}
              onChange={(e) => setRequest(e.target.value)}
              rows={3}
              placeholder="예: 현재 Kubernetes 1.32 클러스터를 1.37로 업그레이드해도 되는지 분석해줘"
              className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700">목표 버전 (선택사항)</label>
            <input
              type="text"
              list="agent-target-version-options"
              value={targetVersion}
              onChange={(e) => setTargetVersion(e.target.value)}
              placeholder="예: 1.37 (비워두면 위 목표 문장에서 자동으로 추출을 시도합니다)"
              className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            />
            <datalist id="agent-target-version-options">
              {targetVersions.map((v) => (
                <option key={v} value={v} />
              ))}
            </datalist>
            <p className="mt-1 text-xs text-slate-400">
              직접 입력할 수 있습니다 — RAG에 아직 문서가 없는 최신 버전도 입력 가능하며, 근거가
              부족한 항목은 추측 없이 "확인 필요"로 명시됩니다.
            </p>
          </div>

          <div className="flex items-center gap-3 rounded-lg border border-slate-200 p-3">
            <input
              id="agent-mock-mode"
              type="checkbox"
              checked={mockMode}
              onChange={(e) => setMockMode(e.target.checked)}
              className="h-4 w-4"
            />
            <label htmlFor="agent-mock-mode" className="text-sm text-slate-700">
              Mock 모드 사용 (실제 클러스터 없이 데모 데이터로 실행)
            </label>
          </div>

          {!mockMode && (
            <div>
              <label className="block text-sm font-medium text-slate-700">kubeconfig</label>
              <input
                type="file"
                onChange={(e) => setKubeconfig(e.target.files?.[0] ?? null)}
                className="mt-1 block w-full text-sm text-slate-600 file:mr-3 file:rounded-md file:border-0 file:bg-slate-100 file:px-3 file:py-2 file:text-sm file:font-medium hover:file:bg-slate-200"
              />
            </div>
          )}

          <div className="rounded-lg border border-slate-200 p-3">
            <p className="text-sm font-medium text-slate-700">LLM 설정 (선택사항)</p>
            <p className="mt-1 text-xs text-slate-500">
              비워두면 목표 해석/최종 요약이 규칙 기반으로만 동작합니다 (증거 판정 자체는
              LLM과 무관하게 항상 결정론적입니다).
            </p>
            <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label className="block text-xs font-medium text-slate-600">LLM Endpoint</label>
                <input
                  type="text"
                  value={llmEndpoint}
                  onChange={(e) => setLlmEndpoint(e.target.value)}
                  placeholder="http://localhost:11434/v1"
                  className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600">Model</label>
                <input
                  type="text"
                  value={llmModel}
                  onChange={(e) => setLlmModel(e.target.value)}
                  placeholder="gpt-oss:20b"
                  className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
                />
              </div>
            </div>
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="w-full rounded-md bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-50"
          >
            {submitting ? "시작하는 중..." : "에이전트 실행"}
          </button>
        </div>
      </div>

      <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-4 text-xs text-amber-800">
        이 Agent는 Read-Only로 동작합니다. 클러스터 변경 작업(delete/patch/apply/scale/
        drain/upgrade 등)은 자동 실행되지 않고 승인 대기 상태로만 기록됩니다.
      </div>
    </div>
  );
}
