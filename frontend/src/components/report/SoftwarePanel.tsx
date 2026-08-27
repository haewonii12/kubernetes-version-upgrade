import type { ClusterInfo, CompatibilityResult } from "../../types/report";
import Badge from "../Badge";
import SourceRefs from "../SourceRefs";

interface Props {
  cluster: ClusterInfo;
  compatibility: CompatibilityResult[];
}

/** Section 21: Installed Software + Compatibility 상태. */
export default function SoftwarePanel({ cluster, compatibility }: Props) {
  const compatByComponent = new Map(compatibility.map((c) => [c.component, c]));

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-sm font-semibold text-slate-500">Installed Software</h3>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-xs uppercase text-slate-400">
                <th className="py-2 pr-4">Component</th>
                <th className="py-2 pr-4">Version</th>
                <th className="py-2 pr-4">Namespace</th>
                <th className="py-2 pr-4">호환성 (최초 발생 버전)</th>
              </tr>
            </thead>
            <tbody>
              {cluster.software_inventory.map((sw) => {
                const compat = compatByComponent.get(sw.name.toLowerCase().replace(/ /g, "-"));
                return (
                  <tr key={`${sw.name}-${sw.namespace}`} className="border-b border-slate-100 align-top">
                    <td className="py-2 pr-4 font-medium text-slate-800">{sw.name}</td>
                    <td className="py-2 pr-4">{sw.version ?? "-"}</td>
                    <td className="py-2 pr-4 text-slate-500">{sw.namespace}</td>
                    <td className="py-2 pr-4">
                      {compat ? (
                        <span className="flex items-center gap-1.5">
                          <Badge label={compat.status} />
                          <span className="text-xs text-slate-400">Kubernetes {compat.target_kubernetes_version}</span>
                        </span>
                      ) : (
                        <Badge label="UNKNOWN" />
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-sm font-semibold text-slate-500">Compatibility 상세 (근거 포함)</h3>
        <div className="mt-3 divide-y divide-slate-100">
          {compatibility.map((c, i) => (
            <div key={i} className="py-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-medium text-slate-800">
                  {c.component} {c.current_version ? `(${c.current_version})` : ""}
                </span>
                <Badge label={c.status} />
                <span className="text-xs text-slate-400">Kubernetes {c.target_kubernetes_version}</span>
              </div>
              <p className="mt-1 text-sm text-slate-600">{c.reason}</p>
              {c.recommendation && <p className="mt-0.5 text-sm text-slate-500">권장: {c.recommendation}</p>}
              <SourceRefs sources={c.sources} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
