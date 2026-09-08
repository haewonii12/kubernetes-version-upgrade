import { useState } from "react";
import type { AgentReport } from "../types/agent";
import type { RiskFinding } from "../types/report";
import Badge from "../components/Badge";

interface Props {
  report: AgentReport;
  onReset: () => void;
}

const TASK_STATUS_STYLE: Record<string, string> = {
  DONE: "bg-emerald-500 text-white",
  FAILED: "bg-red-600 text-white",
  SKIPPED: "bg-slate-300 text-slate-800",
  PENDING: "bg-slate-100 text-slate-500",
  RUNNING: "bg-sky-200 text-sky-900",
};

export default function AgentReportPage({ report, onReset }: Props) {
  const { goal, plan_history, observations, tool_calls, final_conclusion, proposed_actions } = report;
  const { readiness, top_risks, unresolved_components, deprecated_action_required_count } = final_conclusion;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">실행 결과</h2>
            <p className="mt-1 text-sm text-slate-500">{goal.goal}</p>
          </div>
          <span
            className={`shrink-0 rounded-full px-3 py-1 text-xs font-semibold ${
              final_conclusion.goal_met ? "bg-emerald-500 text-white" : "bg-amber-400 text-amber-950"
            }`}
          >
            {final_conclusion.goal_met ? "목표 달성" : "증거 불충분"}
          </span>
        </div>

        <p className="mt-4 text-sm leading-relaxed text-slate-800">{final_conclusion.summary}</p>
        <p className="mt-2 text-xs text-slate-400">종료 사유: {final_conclusion.stopped_reason}</p>
      </div>

      {readiness && (
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-900">업그레이드 준비 복잡도</h3>
            <span className="text-2xl font-bold text-slate-900">{readiness.complexity}%</span>
          </div>
          <div className="mt-4 grid grid-cols-3 gap-3 sm:grid-cols-5">
            <StatCard label="BLOCKER" value={readiness.blocker_count} />
            <StatCard label="HIGH" value={readiness.high_count} />
            <StatCard label="MEDIUM" value={readiness.medium_count} />
            <StatCard label="LOW" value={readiness.low_count} />
            <StatCard label="INFO" value={readiness.info_count} />
          </div>
          {deprecated_action_required_count > 0 && (
            <p className="mt-3 text-xs text-slate-500">
              Deprecated/Removed API 조치 필요: <span className="font-semibold text-slate-700">{deprecated_action_required_count}건</span>
            </p>
          )}
        </div>
      )}

      {top_risks.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
          <h3 className="px-6 pt-6 text-sm font-semibold text-slate-900">주요 Risk</h3>
          <ul className="mt-3 divide-y divide-slate-100">
            {top_risks.map((risk, i) => (
              <RiskRow key={i} risk={risk} />
            ))}
          </ul>
        </div>
      )}

      {unresolved_components.length > 0 && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-6">
          <h3 className="text-sm font-semibold text-amber-800">수동 확인 필요 컴포넌트 ({unresolved_components.length}개)</h3>
          <div className="mt-3 flex flex-wrap gap-1.5">
            {unresolved_components.map((name) => (
              <span key={name} className="rounded-full bg-white px-2.5 py-1 text-xs font-medium text-amber-800 shadow-sm">
                {name}
              </span>
            ))}
          </div>
        </div>
      )}

      {final_conclusion.missing_evidence.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-xs font-semibold text-slate-500">Critic 판단 (불충분 사유)</p>
          <ul className="mt-1 list-inside list-disc space-y-0.5 text-xs text-slate-500">
            {final_conclusion.missing_evidence.map((m, i) => (
              <li key={i}>{m}</li>
            ))}
          </ul>
        </div>
      )}

      {proposed_actions.length > 0 && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-6">
          <h3 className="text-sm font-semibold text-red-800">승인 대기 중인 제안 작업 (자동 실행되지 않음)</h3>
          <ul className="mt-2 space-y-2">
            {proposed_actions.map((action) => (
              <li key={action.id} className="text-sm text-red-900">
                {action.description}{" "}
                <span className="text-xs text-red-600">({action.approval_status})</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <details className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <summary className="cursor-pointer text-sm font-semibold text-slate-900">계획 이력 ({plan_history.length})</summary>
        <ul className="mt-3 space-y-2">
          {plan_history.map((task) => (
            <li key={task.id} className="flex items-center justify-between gap-3 text-sm">
              <div>
                <span className="text-slate-800">{task.description}</span>
                <span className="ml-2 text-xs text-slate-400">({task.tool_name})</span>
                {task.origin === "replan" && (
                  <span className="ml-2 rounded-full bg-indigo-100 px-2 py-0.5 text-xs text-indigo-700">동적 추가</span>
                )}
              </div>
              <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${TASK_STATUS_STYLE[task.status] ?? ""}`}>
                {task.status}
              </span>
            </li>
          ))}
        </ul>
      </details>

      <details className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <summary className="cursor-pointer text-sm font-semibold text-slate-900">관찰 ({observations.length})</summary>
        <ul className="mt-3 space-y-3">
          {observations.map((obs) => (
            <li key={obs.id} className="border-l-2 border-slate-200 pl-3 text-sm">
              <p className="text-slate-800">{obs.observation}</p>
              {obs.impact && <p className="mt-0.5 text-xs text-amber-700">{obs.impact}</p>}
            </li>
          ))}
        </ul>
      </details>

      <CitationsPanel citations={final_conclusion.citations} />

      <details className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <summary className="cursor-pointer text-sm font-semibold text-slate-900">Tool 호출 이력 ({tool_calls.length})</summary>
        <ul className="mt-3 space-y-1">
          {tool_calls.map((call) => (
            <li key={call.id} className="flex items-center gap-2 text-xs text-slate-500">
              <span className={call.ok ? "text-emerald-600" : "text-red-600"}>{call.ok ? "✓" : "✗"}</span>
              {call.tool_name}
              {call.not_configured && <span className="text-slate-400">(미설정)</span>}
            </li>
          ))}
        </ul>
      </details>

      <button
        onClick={onReset}
        className="w-full rounded-md border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
      >
        새 목표 실행
      </button>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-slate-200 p-3 text-center">
      <p className="text-lg font-bold text-slate-900">{value}</p>
      <p className="text-xs text-slate-500">{label}</p>
    </div>
  );
}

function RiskRow({ risk }: { risk: RiskFinding }) {
  const [open, setOpen] = useState(false);
  return (
    <li>
      <button onClick={() => setOpen(!open)} className="flex w-full items-center gap-3 px-6 py-3 text-left hover:bg-slate-50">
        <Badge label={risk.severity} />
        <span className="flex-1 text-sm text-slate-800">{risk.finding}</span>
        <span className="text-slate-400">{open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <div className="space-y-1 bg-slate-50 px-6 py-3 text-sm">
          <p>
            <span className="font-semibold text-slate-600">권장 조치: </span>
            {risk.recommendation}
          </p>
          {risk.reason && (
            <p className="text-xs text-slate-500">
              <span className="font-semibold">사유: </span>
              {risk.reason}
            </p>
          )}
        </div>
      )}
    </li>
  );
}

function CitationsPanel({ citations }: { citations: AgentReport["final_conclusion"]["citations"] }) {
  const bySource = new Map<string, typeof citations>();
  for (const c of citations) {
    const list = bySource.get(c.source_type) ?? [];
    list.push(c);
    bySource.set(c.source_type, list);
  }

  return (
    <details className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <summary className="cursor-pointer text-sm font-semibold text-slate-900">근거 출처 ({citations.length})</summary>
      {citations.length === 0 && <p className="mt-3 text-xs text-slate-400">수집된 근거 없음</p>}
      <div className="mt-3 space-y-4">
        {Array.from(bySource.entries()).map(([source, items]) => (
          <div key={source}>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
              {source} ({items.length})
            </p>
            <ul className="mt-1 space-y-1">
              {items.map((ev, i) => (
                <li key={i} className="text-xs text-slate-500">
                  {ev.url ? (
                    <a href={ev.url} target="_blank" rel="noreferrer" className="underline">
                      {ev.title}
                    </a>
                  ) : (
                    ev.title
                  )}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </details>
  );
}
