import { useEffect, useRef, useState } from "react";
import { agentEventsUrl, getAgentGoalReport } from "../api/agentClient";
import { useEventSource } from "../hooks/useEventSource";
import type { AgentReport, AgentUIEvent } from "../types/agent";

const STAGE_LABELS: Record<string, string> = {
  GOAL: "목표 파싱",
  PLANNING: "계획 수립",
  EXECUTING: "Tool 실행",
  OBSERVING: "결과 관찰",
  EVALUATING: "충분성 판단",
  REPLANNING: "재계획",
  COMPLETED: "완료",
  FAILED: "실패",
};

const STALL_WARNING_SECONDS = 30;
const STALL_ABORT_SECONDS = 90;

interface Props {
  runId: string;
  onComplete: (report: AgentReport) => void;
  onError: (message: string) => void;
}

export default function AgentRunPage({ runId, onComplete, onError }: Props) {
  const [events, setEvents] = useState<AgentUIEvent[]>([]);
  const [secondsSinceLastEvent, setSecondsSinceLastEvent] = useState(0);
  const finishedRef = useRef(false);
  const lastEventAtRef = useRef(Date.now());

  useEffect(() => {
    finishedRef.current = false;
    lastEventAtRef.current = Date.now();
  }, [runId]);

  useEventSource<AgentUIEvent>(
    agentEventsUrl(runId),
    async (event) => {
      lastEventAtRef.current = Date.now();
      setEvents((prev) => [...prev, event]);
      if (finishedRef.current) return;
      if (event.stage === "COMPLETED") {
        finishedRef.current = true;
        try {
          const report = await getAgentGoalReport(runId);
          onComplete(report);
        } catch (e) {
          onError(e instanceof Error ? e.message : "리포트 조회에 실패했습니다.");
        }
      } else if (event.stage === "FAILED") {
        finishedRef.current = true;
        onError(event.message);
      }
    },
    () => {
      // 서버가 스트림을 정상 종료하면 EventSource가 error를 발생시키기도 하므로 무시.
    },
  );

  useEffect(() => {
    const timer = window.setInterval(() => {
      if (finishedRef.current) return;
      const elapsed = Math.floor((Date.now() - lastEventAtRef.current) / 1000);
      setSecondsSinceLastEvent(elapsed);
      if (elapsed >= STALL_ABORT_SECONDS) {
        finishedRef.current = true;
        onError(
          `${STALL_ABORT_SECONDS}초 동안 진행 상황이 업데이트되지 않았습니다. ` +
            "네트워크 연결 또는 백엔드 상태를 확인한 뒤 다시 시도해주세요.",
        );
      }
    }, 1000);
    return () => window.clearInterval(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runId]);

  const latest = events[events.length - 1];
  const progress = latest?.progress ?? 0;
  const isStalled = secondsSinceLastEvent >= STALL_WARNING_SECONDS;

  return (
    <div className="mx-auto max-w-xl">
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">자율 에이전트 실행 중</h2>
        <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-slate-100">
          <div
            className="h-full rounded-full bg-slate-900 transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="mt-2 text-right text-xs text-slate-400">
          {progress}% {latest ? `· iteration ${latest.iteration}` : ""}
        </p>

        {isStalled && (
          <p className="mt-3 rounded-md bg-amber-50 px-3 py-2 text-xs text-amber-700">
            {secondsSinceLastEvent}초째 진행 상황 업데이트가 없습니다 (최대 {STALL_ABORT_SECONDS}초
            후 자동으로 중단됩니다).
          </p>
        )}

        <ul className="mt-4 max-h-96 space-y-2 overflow-y-auto">
          {events.map((event, idx) => (
            <li key={idx} className="flex items-start gap-2 text-sm">
              <span className="mt-0.5 shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
                {STAGE_LABELS[event.stage] ?? event.stage}
              </span>
              <span className="text-slate-700">{event.message}</span>
            </li>
          ))}
          {events.length === 0 && <li className="text-sm text-slate-400">연결 중...</li>}
        </ul>
      </div>
    </div>
  );
}
