// backend/app/models/agent.py 를 1:1로 미러링한다.

import type { ReadinessScore, RiskFinding } from "./report";

export type ToolCapability =
  | "cluster_read"
  | "compatibility"
  | "deprecated_api"
  | "risk"
  | "knowledge_search"
  | "web_search"
  | "official_docs"
  | "source_code"
  | "observability"
  | "gitops";

export interface Goal {
  goal: string;
  target_version: string | null;
  success_criteria: string[];
  created_at: string;
}

export type TaskStatus = "PENDING" | "RUNNING" | "DONE" | "FAILED" | "SKIPPED";

export interface AgentTask {
  id: string;
  description: string;
  capability_hint: ToolCapability | null;
  tool_name: string | null;
  input: Record<string, unknown>;
  expected_outcome: string | null;
  status: TaskStatus;
  origin: string;
  subject_key: string | null;
  created_at_iteration: number;
}

export interface Evidence {
  source_type: string;
  title: string;
  url: string | null;
  doc_id: string | null;
  excerpt: string | null;
  retrieved_at: string | null;
}

export interface Observation {
  id: string;
  task_id: string;
  tool_name: string;
  observation: string;
  expected: string | null;
  actual: string | null;
  impact: string | null;
  requires_further_investigation: boolean;
  follow_up_hint: Record<string, unknown> | null;
  evidence: Evidence[];
  created_at_iteration: number;
}

export interface ToolCallRecord {
  id: string;
  task_id: string;
  tool_name: string;
  started_at: string;
  finished_at: string | null;
  ok: boolean | null;
  not_configured: boolean;
  error: string | null;
}

export type ApprovalStatus = "NOT_REQUIRED" | "PENDING" | "APPROVED" | "REJECTED";

export interface ProposedAction {
  id: string;
  description: string;
  verb: string;
  target: string | null;
  command: string | null;
  approval_status: ApprovalStatus;
  created_at_iteration: number;
}

export interface FinalConclusion {
  summary: string;
  goal_met: boolean;
  missing_evidence: string[];
  citations: Evidence[];
  stopped_reason: string;
  readiness: ReadinessScore | null;
  top_risks: RiskFinding[];
  unresolved_components: string[];
  deprecated_action_required_count: number;
}

export interface AgentReport {
  run_id: string;
  created_at: string;
  goal: Goal;
  plan_history: AgentTask[];
  observations: Observation[];
  tool_calls: ToolCallRecord[];
  final_conclusion: FinalConclusion;
  proposed_actions: ProposedAction[];
}

/** SSE로 실제 전송되는 페이로드 (models.agent.AgentUIEvent). */
export interface AgentUIEvent {
  stage: string;
  event_type: string;
  message: string;
  timestamp: string;
  progress: number;
  iteration: number;
  detail: Record<string, unknown>;
}

export interface AgentGoalStatus {
  run_id: string;
  status: "RUNNING" | "COMPLETED" | "FAILED";
  raw_request: string;
  target_version: string | null;
  mock_mode: boolean;
  latest_event: AgentUIEvent | null;
  error: string | null;
}
