import type { AgentGoalStatus, AgentReport } from "../types/agent";

const BASE = "/api/v1/agent";

async function handleJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(text || `요청 실패 (${res.status})`);
  }
  return res.json() as Promise<T>;
}

export async function createAgentGoal(
  request: string,
  targetVersion: string,
  mockMode: boolean,
  kubeconfig: File | null,
  llmOptions?: { llmEndpoint?: string; llmModel?: string },
): Promise<string> {
  const form = new FormData();
  form.append("request", request);
  if (targetVersion) {
    form.append("target_kubernetes_version", targetVersion);
  }
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
  const res = await fetch(`${BASE}/goals`, { method: "POST", body: form });
  const data = await handleJson<{ run_id: string }>(res);
  return data.run_id;
}

export async function getAgentGoalStatus(runId: string): Promise<AgentGoalStatus> {
  const res = await fetch(`${BASE}/goals/${runId}`);
  return handleJson<AgentGoalStatus>(res);
}

export async function getAgentGoalReport(runId: string): Promise<AgentReport> {
  const res = await fetch(`${BASE}/goals/${runId}/report`);
  return handleJson<AgentReport>(res);
}

/** useEventSource(agentEventsUrl(runId), ...) 형태로 직접 넘겨 쓴다. */
export function agentEventsUrl(runId: string): string {
  return `${BASE}/goals/${runId}/events`;
}
