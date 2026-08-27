import { useState } from "react";
import type { ReadinessScore, RiskFinding } from "../../types/report";
import Badge from "../Badge";
import SourceRefs from "../SourceRefs";

const SEVERITY_ORDER = ["BLOCKER", "HIGH", "MEDIUM", "LOW", "INFO"];

interface Props {
  risks: RiskFinding[];
  readiness: ReadinessScore;
}

/** Section 22: Risk Dashboard — 클릭 시 상세 내용을 펼쳐서 보여준다. */
export default function RiskPanel({ risks, readiness }: Props) {
  const [expanded, setExpanded] = useState<number | null>(null);
  const sorted = [...risks].sort(
    (a, b) => SEVERITY_ORDER.indexOf(a.severity) - SEVERITY_ORDER.indexOf(b.severity),
  );

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
        <CountCard label="BLOCKER" value={readiness.blocker_count} />
        <CountCard label="HIGH" value={readiness.high_count} />
        <CountCard label="MEDIUM" value={readiness.medium_count} />
        <CountCard label="LOW" value={readiness.low_count} />
        <CountCard label="INFO" value={readiness.info_count} />
      </div>

      <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
        <ul className="divide-y divide-slate-100">
          {sorted.map((risk, i) => {
            const isOpen = expanded === i;
            return (
              <li key={i}>
                <button
                  onClick={() => setExpanded(isOpen ? null : i)}
                  className="flex w-full items-center gap-3 px-6 py-3 text-left hover:bg-slate-50"
                >
                  <Badge label={risk.severity} />
                  <span className="flex-1 text-sm text-slate-800">{risk.finding}</span>
                  <span className="text-xs text-slate-400">{risk.category}</span>
                  <span className="text-slate-400">{isOpen ? "▲" : "▼"}</span>
                </button>
                {isOpen && (
                  <div className="space-y-2 bg-slate-50 px-6 py-4 text-sm">
                    <p>
                      <span className="font-semibold text-slate-600">사유: </span>
                      {risk.reason}
                    </p>
                    <p>
                      <span className="font-semibold text-slate-600">권장 조치: </span>
                      {risk.recommendation}
                    </p>
                    {risk.related_upgrade_step && (
                      <p className="text-xs text-slate-500">관련 Upgrade 단계: {risk.related_upgrade_step}</p>
                    )}
                    <SourceRefs sources={risk.sources} />
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}

function CountCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 text-center shadow-sm">
      <p className="text-xl font-bold text-slate-900">{value}</p>
      <p className="text-xs text-slate-500">{label}</p>
    </div>
  );
}
