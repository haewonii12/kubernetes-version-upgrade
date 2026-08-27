import type { DeprecatedAPIFinding } from "../../types/report";
import Badge from "../Badge";
import SourceRefs from "../SourceRefs";

/** Section 11/20: Deprecated / Removed API 검사 결과. */
export default function DeprecatedApiPanel({ findings }: { findings: DeprecatedAPIFinding[] }) {
  if (findings.length === 0) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-500 shadow-sm">
        검사 대상 리소스 중 Deprecated/Removed API 문제가 발견되지 않았습니다.
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-500">Deprecated / Removed APIs</h3>
      <div className="mt-3 divide-y divide-slate-100">
        {findings.map((f, i) => (
          <div key={i} className="py-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-medium text-slate-800">
                {f.resource_kind} {f.resource_name ? `— ${f.namespace ? `${f.namespace}/` : ""}${f.resource_name}` : ""}
              </span>
              <Badge label={f.status} />
            </div>
            <p className="mt-1 font-mono text-xs text-slate-500">apiVersion: {f.api_version}</p>
            <dl className="mt-1 grid grid-cols-2 gap-x-4 text-xs text-slate-500 sm:grid-cols-3">
              {f.deprecated_in_version && <div>Deprecated: Kubernetes {f.deprecated_in_version}</div>}
              {f.removed_in_version && <div>Removed: Kubernetes {f.removed_in_version}</div>}
              {f.replacement_api_version && <div>대체 API: {f.replacement_api_version}</div>}
            </dl>
            <SourceRefs sources={f.sources} />
          </div>
        ))}
      </div>
    </div>
  );
}
