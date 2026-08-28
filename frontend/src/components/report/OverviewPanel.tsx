import type { ComplexityFactor, ReadinessScore, UpgradeReport } from "../../types/report";

const SEVERITY_LABEL: Record<string, string> = {
  BLOCKER: "BLOCKER",
  HIGH: "HIGH",
  MEDIUM: "MEDIUM",
  LOW: "LOW",
  INFO: "INFO",
};

/** Section 19: 분석 완료 후 Dashboard 결과 화면. */
export default function OverviewPanel({ report }: { report: UpgradeReport }) {
  const { readiness, upgrade_plan, cluster } = report;
  const minors = upgrade_plan.upgrade_path.map((v) => v.split(".").slice(0, 2).join("."));

  return (
    <div className="space-y-6">
      {report.executive_summary && (
        <div className="rounded-xl border border-indigo-200 bg-indigo-50 p-5 shadow-sm">
          <div className="flex items-center gap-2">
            <span className="badge bg-indigo-600 text-white">AI 요약</span>
            <h3 className="text-sm font-semibold text-indigo-900">전체 요약</h3>
          </div>
          <p className="mt-2 text-sm leading-relaxed text-indigo-950">{report.executive_summary}</p>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard label="Current" value={`Kubernetes ${upgrade_plan.current_version}`} />
        <StatCard label="Target" value={`Kubernetes ${upgrade_plan.target_version}`} />
        <ComplexityCard readiness={readiness} />
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-sm font-semibold text-slate-500">Upgrade Path</h3>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          {minors.map((m, i) => (
            <div key={i} className="flex items-center gap-2">
              <span className="rounded-lg border border-slate-300 bg-slate-50 px-3 py-1.5 text-sm font-medium text-slate-800">
                {m}
              </span>
              {i < minors.length - 1 && <span className="text-slate-400">→</span>}
            </div>
          ))}
        </div>
        <p className="mt-3 text-xs text-slate-500">
          minor version을 건너뛰지 않고 한 단계씩 순차적으로 업그레이드합니다 (Version Skew Policy 기준).
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
        <CountCard label="BLOCKER" value={readiness.blocker_count} color="bg-red-600" />
        <CountCard label="HIGH" value={readiness.high_count} color="bg-orange-500" />
        <CountCard label="MEDIUM" value={readiness.medium_count} color="bg-amber-400" />
        <CountCard label="LOW" value={readiness.low_count} color="bg-sky-300" />
        <CountCard label="INFO" value={readiness.info_count} color="bg-slate-300" />
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-sm font-semibold text-slate-500">클러스터 요약</h3>
        <dl className="mt-3 grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
          <Summary term="Control Plane" desc={`${cluster.control_plane.node_count}대 (${cluster.control_plane.is_ha ? "HA" : "단일"})`} />
          <Summary term="Worker" desc={`${cluster.worker_node_count}대`} />
          <Summary term="etcd" desc={cluster.etcd.topology} />
          <Summary term="CNI" desc={cluster.cni ? `${cluster.cni} ${cluster.cni_version ?? ""}` : "확인 안됨"} />
        </dl>
      </div>
    </div>
  );
}

function StatCard({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{label}</p>
      <p className={`mt-1 text-2xl font-bold ${accent ?? "text-slate-900"}`}>{value}</p>
    </div>
  );
}

function ComplexityCard({ readiness }: { readiness: ReadinessScore }) {
  const c = readiness.complexity;
  const accent = c >= 50 ? "text-red-600" : c >= 20 ? "text-amber-600" : "text-emerald-600";
  const level = c >= 50 ? "복잡" : c >= 20 ? "보통" : "단순";
  const factors: ComplexityFactor[] = readiness.complexity_factors ?? [];
  const rawSum = factors.reduce((s, f) => s + f.points, 0);

  return (
    <div className="group relative rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="flex items-center gap-1 text-xs font-medium uppercase tracking-wide text-slate-400">
        업그레이드 준비 복잡도
        <span className="text-slate-300" aria-hidden>
          ⓘ
        </span>
      </p>
      <p className={`mt-1 text-2xl font-bold ${accent}`}>
        {c}% <span className="text-sm font-medium">· {level}</span>
      </p>
      <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
        <div
          className={`h-full rounded-full ${c >= 50 ? "bg-red-500" : c >= 20 ? "bg-amber-400" : "bg-emerald-500"}`}
          style={{ width: `${c}%` }}
        />
      </div>

      <div className="pointer-events-none absolute left-0 top-full z-10 mt-2 w-80 rounded-lg border border-slate-200 bg-white p-3 text-left text-xs opacity-0 shadow-lg transition-opacity duration-150 group-hover:opacity-100">
        <p className="text-slate-600">
          발견된 Risk를 심각도별로 가중 합산한 값입니다 (0% = 특이사항 없음, 100% = 상한).
          <span className="text-slate-400"> INFO는 반영하지 않습니다.</span>
        </p>
        {factors.length > 0 ? (
          <table className="mt-2 w-full">
            <tbody>
              {factors.map((f) => (
                <tr key={f.severity} className="text-slate-700">
                  <td className="py-0.5 pr-2 font-medium">{SEVERITY_LABEL[f.severity] ?? f.severity}</td>
                  <td className="py-0.5 pr-2 text-slate-500">
                    {f.count}건 × {f.weight}
                  </td>
                  <td className="py-0.5 text-right tabular-nums">{f.points}</td>
                </tr>
              ))}
              <tr className="border-t border-slate-200 font-semibold text-slate-800">
                <td className="py-1" colSpan={2}>
                  합계
                </td>
                <td className="py-1 text-right tabular-nums">
                  {rawSum > 100 ? `${rawSum} → 100%` : `${rawSum}%`}
                </td>
              </tr>
            </tbody>
          </table>
        ) : (
          <p className="mt-2 text-slate-500">감점 대상 Risk가 없습니다.</p>
        )}
        <p className="mt-2 text-slate-400">가중치: BLOCKER 20 · HIGH 8 · MEDIUM 3 · LOW 1</p>
      </div>
    </div>
  );
}

function CountCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 text-center shadow-sm">
      <span className={`mx-auto mb-2 flex h-2 w-8 rounded-full ${color}`} />
      <p className="text-xl font-bold text-slate-900">{value}</p>
      <p className="text-xs text-slate-500">{label}</p>
    </div>
  );
}

function Summary({ term, desc }: { term: string; desc: string }) {
  return (
    <div>
      <dt className="text-xs text-slate-400">{term}</dt>
      <dd className="font-medium text-slate-800">{desc}</dd>
    </div>
  );
}
