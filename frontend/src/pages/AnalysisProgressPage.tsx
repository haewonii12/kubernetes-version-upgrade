import { useEffect, useRef, useState } from "react";
import { getReport, subscribeToEvents } from "../api/client";
import type { AnalysisEvent, UpgradeReport } from "../types/report";

const STAGE_ORDER: { key: string; label: string }[] = [
  { key: "CLUSTER_CONNECTION", label: "클러스터 연결" },
  { key: "NODE_SCAN", label: "Kubernetes Version / Node 정보 확인" },
  { key: "OS_KERNEL_SCAN", label: "OS / Kernel / Control Plane HA / etcd 확인" },
  { key: "CUSTOM_CONFIG_SCAN", label: "Custom Configuration 탐지" },
  { key: "ADDON_SCAN", label: "Namespace 전체 Software Inventory / CRD 조사" },
  { key: "RAG_SEARCH", label: "Release Note / Compatibility RAG 검색" },
  { key: "COMPATIBILITY_CHECK", label: "Compatibility 분석" },
  { key: "DEPRECATED_API_CHECK", label: "Deprecated / Removed API 검사" },
  { key: "RISK_ANALYSIS", label: "Risk 분석 및 준비 복잡도 계산" },
  { key: "UPGRADE_PATH_GENERATION", label: "Upgrade Path 생성" },
  { key: "UPGRADE_PLAN_GENERATION", label: "Version별 Upgrade Scenario 생성" },
  { key: "COMPLETED", label: "완료" },
];

// 정체(stall) 감지 임계값 (초). 백엔드가 알 수 없는 이유로 멈추더라도 화면이
// 영원히 "진행 중"처럼 보이지 않도록 하는 방어선이다.
const STALL_WARNING_SECONDS = 30;
const STALL_ABORT_SECONDS = 90;

interface Props {
  analysisId: string;
  onComplete: (report: UpgradeReport) => void;
  onError: (message: string) => void;
}

export default function AnalysisProgressPage({ analysisId, onComplete, onError }: Props) {
  const [events, setEvents] = useState<AnalysisEvent[]>([]);
  const [secondsSinceLastEvent, setSecondsSinceLastEvent] = useState(0);
  const finishedRef = useRef(false);
  const lastEventAtRef = useRef(Date.now());

  useEffect(() => {
    finishedRef.current = false;
    lastEventAtRef.current = Date.now();

    const unsubscribe = subscribeToEvents(
      analysisId,
      async (event) => {
        lastEventAtRef.current = Date.now();
        setEvents((prev) => [...prev, event]);
        if (finishedRef.current) return;
        if (event.stage === "COMPLETED") {
          finishedRef.current = true;
          try {
            const report = await getReport(analysisId);
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
    return unsubscribe;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [analysisId]);

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
  }, [analysisId]);

  const latestStageIndex = events.length
    ? STAGE_ORDER.findIndex((s) => s.key === events[events.length - 1].stage)
    : -1;
  const progress = events.length ? events[events.length - 1].progress : 0;
  const isStalled = secondsSinceLastEvent >= STALL_WARNING_SECONDS;

  return (
    <div className="mx-auto max-w-xl">
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">클러스터 분석 중</h2>
        <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-slate-100">
          <div
            className="h-full rounded-full bg-slate-900 transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="mt-2 text-right text-xs text-slate-400">{progress}%</p>

        {isStalled && (
          <p className="mt-3 rounded-md bg-amber-50 px-3 py-2 text-xs text-amber-700">
            {secondsSinceLastEvent}초째 진행 상황 업데이트가 없습니다. 분석이 지연되고
            있을 수 있습니다 (최대 {STALL_ABORT_SECONDS}초 후 자동으로 중단됩니다).
          </p>
        )}

        <ul className="mt-4 space-y-2">
          {STAGE_ORDER.map((stage, idx) => {
            const done = idx <= latestStageIndex;
            const active = idx === latestStageIndex && stage.key !== "COMPLETED";
            return (
              <li key={stage.key} className="flex items-center gap-2 text-sm">
                <span
                  className={
                    done
                      ? "flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500 text-xs text-white"
                      : "flex h-5 w-5 items-center justify-center rounded-full border border-slate-300 text-xs text-transparent"
                  }
                >
                  ✓
                </span>
                <span className={done ? "text-slate-800" : active ? "text-slate-600" : "text-slate-400"}>
                  {stage.label}
                </span>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
