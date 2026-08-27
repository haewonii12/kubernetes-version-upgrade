import { useState } from "react";
import type { VersionUpgradePhase } from "../../types/report";
import Badge from "../Badge";
import CommandBlock from "../CommandBlock";
import SourceRefs from "../SourceRefs";

/** Section 16/23: Version별 Upgrade Scenario Timeline. 단계를 펼쳐 상세 내용을 본다. */
export default function TimelinePanel({ phases }: { phases: VersionUpgradePhase[] }) {
  const [openPhase, setOpenPhase] = useState<number>(phases[0]?.phase_number ?? 1);

  return (
    <div className="space-y-4">
      {phases.map((phase) => {
        const isOpen = openPhase === phase.phase_number;
        return (
          <div key={phase.phase_number} className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
            <button
              onClick={() => setOpenPhase(isOpen ? -1 : phase.phase_number)}
              className="flex w-full items-center justify-between px-6 py-4 text-left hover:bg-slate-50"
            >
              <span className="font-semibold text-slate-900">
                Phase {phase.phase_number}: {phase.from_version} → {phase.to_version}
              </span>
              <span className="text-slate-400">{isOpen ? "▲" : "▼"}</span>
            </button>

            {isOpen && (
              <div className="space-y-6 border-t border-slate-100 px-6 py-5">
                {phase.release_note_summary && (
                  <section>
                    <div className="flex items-center gap-2">
                      <h4 className="text-xs font-semibold uppercase text-slate-400">Release Note 요약</h4>
                      {phase.release_note_summary_source === "llm" && (
                        <span className="badge bg-indigo-600 text-white">AI 생성</span>
                      )}
                    </div>
                    <p className="mt-1 text-sm text-slate-600">{phase.release_note_summary}</p>
                    <SourceRefs sources={phase.sources} />
                  </section>
                )}

                <section>
                  <h4 className="text-xs font-semibold uppercase text-slate-400">Pre Check</h4>
                  <CheckList items={phase.pre_checks} />
                </section>

                {phase.compatibility_results.length > 0 && (
                  <section>
                    <h4 className="text-xs font-semibold uppercase text-slate-400">Compatibility (이 단계 기준)</h4>
                    <ul className="mt-2 space-y-1">
                      {phase.compatibility_results
                        .filter((c) => c.status !== "COMPATIBLE")
                        .map((c, i) => (
                          <li key={i} className="flex items-center gap-2 text-sm">
                            <Badge label={c.status} />
                            <span>{c.component}</span>
                            <span className="text-xs text-slate-400">{c.reason}</span>
                          </li>
                        ))}
                    </ul>
                  </section>
                )}

                {phase.deprecated_apis.length > 0 && (
                  <section>
                    <h4 className="text-xs font-semibold uppercase text-slate-400">Deprecated / Removed API</h4>
                    <ul className="mt-2 space-y-1">
                      {phase.deprecated_apis.map((d, i) => (
                        <li key={i} className="flex items-center gap-2 text-sm">
                          <Badge label={d.status} />
                          <span>
                            {d.resource_kind} ({d.api_version})
                          </span>
                        </li>
                      ))}
                    </ul>
                  </section>
                )}

                <section>
                  <h4 className="text-xs font-semibold uppercase text-slate-400">Control Plane Upgrade (순차)</h4>
                  <div className="mt-2 space-y-3">
                    {phase.control_plane_steps.map((step) => (
                      <div key={step.node} className="rounded-lg bg-slate-50 p-3">
                        <p className="text-sm font-medium text-slate-700">
                          {step.order}. {step.node}
                        </p>
                        <div className="mt-2">
                          <CommandBlock commands={step.commands} />
                        </div>
                        <p className="mt-2 text-xs text-slate-400">검증: {step.verification.join(", ")}</p>
                      </div>
                    ))}
                  </div>
                </section>

                {phase.worker_steps.length > 0 && (
                  <section>
                    <h4 className="text-xs font-semibold uppercase text-slate-400">Worker Upgrade</h4>
                    <div className="mt-2 space-y-3">
                      {phase.worker_steps.map((step) => (
                        <div key={step.node} className="rounded-lg bg-slate-50 p-3">
                          <p className="text-sm font-medium text-slate-700">{step.node}</p>
                          <div className="mt-2">
                            <CommandBlock commands={step.commands} />
                          </div>
                        </div>
                      ))}
                    </div>
                  </section>
                )}

                <section>
                  <h4 className="text-xs font-semibold uppercase text-slate-400">Post Check</h4>
                  <CheckList items={phase.post_checks} />
                </section>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function CheckList({ items }: { items: { description: string; command: string | null }[] }) {
  return (
    <ul className="mt-2 space-y-1.5">
      {items.map((item, i) => (
        <li key={i} className="text-sm text-slate-700">
          <span>• {item.description}</span>
          {item.command && (
            <code className="mt-1 block rounded bg-slate-900 px-2 py-1 text-xs text-emerald-300 overflow-x-auto">
              $ {item.command}
            </code>
          )}
        </li>
      ))}
    </ul>
  );
}
