import { useEffect, useState } from "react";
import { createAnalysis, listTargetVersions } from "../api/client";

interface Props {
  onStarted: (analysisId: string) => void;
}

export default function ConnectionPage({ onStarted }: Props) {
  const [mockMode, setMockMode] = useState(true);
  const [targetVersions, setTargetVersions] = useState<string[]>([]);
  const [targetVersion, setTargetVersion] = useState("");
  const [versionsError, setVersionsError] = useState<string | null>(null);
  const [kubeconfig, setKubeconfig] = useState<File | null>(null);
  const [llmEndpoint, setLlmEndpoint] = useState("");
  const [llmModel, setLlmModel] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listTargetVersions()
      .then((versions) => {
        setTargetVersions(versions);
        if (versions.length > 0) {
          setTargetVersion(versions[versions.length - 1]);
        }
      })
      .catch((e) => {
        setVersionsError(
          e instanceof Error ? e.message : "Target Version 목록을 불러오지 못했습니다.",
        );
      });
  }, []);

  async function handleSubmit() {
    setError(null);
    if (!targetVersion) {
      setError("Target Kubernetes Version을 선택할 수 없습니다 (목록을 불러오지 못했습니다).");
      return;
    }
    if (!mockMode && !kubeconfig) {
      setError("실제 클러스터 분석을 하려면 kubeconfig 파일을 업로드해야 합니다.");
      return;
    }
    setSubmitting(true);
    try {
      const id = await createAnalysis(targetVersion, mockMode, kubeconfig, {
        llmEndpoint: llmEndpoint.trim() || undefined,
        llmModel: llmModel.trim() || undefined,
      });
      onStarted(id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "분석 시작에 실패했습니다.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-xl">
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">클러스터 연결</h2>
        <p className="mt-1 text-sm text-slate-500">
          kubeconfig를 업로드하면 분석이 끝난 직후 서버에서 즉시 삭제됩니다. Mock 모드에서는
          업로드 없이 데모 클러스터 데이터로 전체 파이프라인을 체험할 수 있습니다.
        </p>

        <div className="mt-6 space-y-5">
          <div className="flex items-center gap-3 rounded-lg border border-slate-200 p-3">
            <input
              id="mock-mode"
              type="checkbox"
              checked={mockMode}
              onChange={(e) => setMockMode(e.target.checked)}
              className="h-4 w-4"
            />
            <label htmlFor="mock-mode" className="text-sm text-slate-700">
              Mock 모드 사용 (실제 클러스터 없이 데모 데이터로 분석)
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

          <div>
            <label className="block text-sm font-medium text-slate-700">Target Kubernetes Version</label>
            <select
              value={targetVersion}
              onChange={(e) => setTargetVersion(e.target.value)}
              disabled={targetVersions.length === 0}
              className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm disabled:bg-slate-50 disabled:text-slate-400"
            >
              {targetVersions.length === 0 && <option value="">불러오는 중...</option>}
              {targetVersions.map((v) => (
                <option key={v} value={v}>
                  Kubernetes {v}
                </option>
              ))}
            </select>
            <p className="mt-1 text-xs text-slate-400">
              이 목록은 RAG의 Release Note 문서(rag/documents/release-notes/)에 등록된
              버전에서 자동으로 가져옵니다. 새 버전 문서를 추가하면 여기에도 반영됩니다.
            </p>
            {versionsError && <p className="mt-1 text-xs text-red-600">{versionsError}</p>}
          </div>

          <div className="rounded-lg border border-slate-200 p-3">
            <p className="text-sm font-medium text-slate-700">LLM 설정 (선택사항)</p>
            <p className="mt-1 text-xs text-slate-500">
              비워두면 RAG 검색 결과 원문만 표시됩니다. 입력하면 Release Note 요약과 전체
              요약을 LLM이 생성합니다 (Compatibility/Risk 판정 자체는 LLM과 무관하게 항상
              RAG 규칙 기반입니다). 입력한 주소로만 요청하며 그 외 외부 전송은 없습니다.
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
            <p className="mt-2 text-xs text-slate-400">
              OpenAI 호환 <code>/chat/completions</code> API를 쓰는 서버(Ollama, vLLM,
              LM Studio 등)를 지원합니다.
            </p>
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="w-full rounded-md bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-50"
          >
            {submitting ? "분석 시작 중..." : "클러스터 분석"}
          </button>
        </div>
      </div>

      <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-4 text-xs text-amber-800">
        이 Agent는 Read-Only로 동작합니다. 클러스터에 어떠한 생성/수정/삭제 작업도 수행하지
        않으며, 업그레이드 명령은 실행이 아니라 <strong>제안</strong>으로만 제공됩니다.
      </div>
    </div>
  );
}
