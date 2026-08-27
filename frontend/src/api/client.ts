import type { AnalysisEvent, AnalysisStatus, UpgradeReport } from "../types/report";

const BASE = "/api/v1";

async function handleJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(text || `요청 실패 (${res.status})`);
  }
  return res.json() as Promise<T>;
}

export async function createAnalysis(
  targetVersion: string,
  mockMode: boolean,
  kubeconfig: File | null,
  llmOptions?: { llmEndpoint?: string; llmModel?: string },
): Promise<string> {
  const form = new FormData();
  form.append("target_kubernetes_version", targetVersion);
  form.append("mock_mode", String(mockMode));
  if (kubeconfig) {
    form.append("kubeconfig", kubeconfig);
  }
  if (llmOptions?.llmEndpoint) {
    form.append("llm_endpoint", llmOptions.llmEndpoint);
  }
  if (llmOptions?.llmModel) {
    form.append("llm_model", llmOptions.llmModel);
  }
  const res = await fetch(`${BASE}/analysis`, { method: "POST", body: form });
  const data = await handleJson<{ analysis_id: string }>(res);
  return data.analysis_id;
}

export async function getAnalysisStatus(analysisId: string): Promise<AnalysisStatus> {
  const res = await fetch(`${BASE}/analysis/${analysisId}`);
  return handleJson<AnalysisStatus>(res);
}

export async function getReport(analysisId: string): Promise<UpgradeReport> {
  const res = await fetch(`${BASE}/analysis/${analysisId}/report`);
  return handleJson<UpgradeReport>(res);
}

/** RAG의 release-notes 문서에 등록된 minor 버전 목록 (하드코딩 아님, Section 9/18). */
export async function listTargetVersions(): Promise<string[]> {
  const res = await fetch(`${BASE}/target-versions`);
  const data = await handleJson<{ versions: string[] }>(res);
  return data.versions;
}

export async function listSnapshots(): Promise<
  { analysis_id: string; created_at: string; kubernetes_version: string; target_version: string; readiness_score: number }[]
> {
  const res = await fetch(`${BASE}/snapshots`);
  return handleJson(res);
}

/** SSE 진행 이벤트 구독. 반환된 함수를 호출하면 구독을 해제한다. */
export function subscribeToEvents(
  analysisId: string,
  onEvent: (event: AnalysisEvent) => void,
  onError?: (err: Event) => void,
): () => void {
  const source = new EventSource(`${BASE}/analysis/${analysisId}/events`);
  source.onmessage = (ev) => {
    try {
      onEvent(JSON.parse(ev.data) as AnalysisEvent);
    } catch {
      // JSON 파싱 실패는 무시 (keep-alive ping 등)
    }
  };
  source.onerror = (err) => {
    onError?.(err);
  };
  return () => source.close();
}
