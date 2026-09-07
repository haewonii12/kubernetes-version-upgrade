import type { AgentReport } from "../types/agent";

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

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-start justify-between">
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

        {final_conclusion.missing_evidence.length > 0 && (
          <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-3">
            <p className="text-xs font-semibold text-amber-800">미해결 사항</p>
            <ul className="mt-1 list-inside list-disc space-y-0.5 text-xs text-amber-800">
              {final_conclusion.missing_evidence.map((m, i) => (
                <li key={i}>{m}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

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

      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-sm font-semibold text-slate-900">계획 이력 ({plan_history.length})</h3>
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
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-sm font-semibold text-slate-900">관찰 ({observations.length})</h3>
        <ul className="mt-3 space-y-3">
          {observations.map((obs) => (
            <li key={obs.id} className="border-l-2 border-slate-200 pl-3 text-sm">
              <p className="text-slate-800">{obs.observation}</p>
              {obs.impact && <p className="mt-0.5 text-xs text-amber-700">{obs.impact}</p>}
            </li>
          ))}
        </ul>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-sm font-semibold text-slate-900">근거 출처 ({final_conclusion.citations.length})</h3>
        <ul className="mt-3 space-y-1">
          {final_conclusion.citations.map((ev, i) => (
            <li key={i} className="text-xs text-slate-500">
              <span className="font-medium text-slate-600">[{ev.source_type}]</span>{" "}
              {ev.url ? (
                <a href={ev.url} target="_blank" rel="noreferrer" className="underline">
                  {ev.title}
                </a>
              ) : (
                ev.title
              )}
            </li>
          ))}
          {final_conclusion.citations.length === 0 && (
            <li className="text-xs text-slate-400">수집된 근거 없음</li>
          )}
        </ul>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-sm font-semibold text-slate-900">Tool 호출 이력 ({tool_calls.length})</h3>
        <ul className="mt-3 space-y-1">
          {tool_calls.map((call) => (
            <li key={call.id} className="flex items-center gap-2 text-xs text-slate-500">
              <span className={call.ok ? "text-emerald-600" : "text-red-600"}>{call.ok ? "✓" : "✗"}</span>
              {call.tool_name}
              {call.not_configured && <span className="text-slate-400">(미설정)</span>}
            </li>
          ))}
        </ul>
      </div>

      <button
        onClick={onReset}
        className="w-full rounded-md border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
      >
        새 목표 실행
      </button>
    </div>
  );
}
