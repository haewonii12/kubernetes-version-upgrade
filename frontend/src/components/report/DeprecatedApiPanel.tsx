import type { DeprecatedAPIFinding } from "../../types/report";
import Badge from "../Badge";
import SourceRefs from "../SourceRefs";

interface Props {
  findings: DeprecatedAPIFinding[];
  plutoSkipped?: string | null;
}

/** Section 11/20: Deprecated / Removed API 검사 결과 (RAG + pluto 하이브리드). */
export default function DeprecatedApiPanel({ findings, plutoSkipped }: Props) {
  return (
    <div className="space-y-4">
      {plutoSkipped && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
          pluto 교차검증을 건너뛰었습니다: {plutoSkipped} (RAG 문서 기반 판정은 정상 수행됨)
        </div>
      )}

      {findings.length === 0 ? (
        <div className="rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-500 shadow-sm">
          라이브 오브젝트 및 Helm 차트 매니페스트에서 Deprecated/Removed API 문제가 발견되지 않았습니다.
        </div>
      ) : (
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-500">Deprecated / Removed APIs</h3>
          <p className="mt-1 text-xs text-slate-400">
            판정 근거: <code>rag</code> = 이 저장소 RAG 문서 · <code>pluto</code> = 번들된 pluto 교차검증 ·{" "}
            <code>helm:…</code> = 아직 적용 안 된 Helm 차트 매니페스트(다음 <code>helm upgrade</code> 시 실패)
          </p>
          <div className="mt-3 divide-y divide-slate-100">
            {findings.map((f, i) => (
              <div key={i} className="py-3">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-medium text-slate-800">
                    {f.resource_kind}
                    {f.resource_name ? ` — ${f.namespace ? `${f.namespace}/` : ""}${f.resource_name}` : ""}
                  </span>
                  <Badge label={f.status} />
                  {f.scanned_by === "pluto" && (
                    <span className="rounded bg-violet-100 px-1.5 py-0.5 text-[10px] font-medium text-violet-700">
                      pluto
                    </span>
                  )}
                  {f.found_in && f.found_in.startsWith("helm:") && (
                    <span className="rounded bg-sky-100 px-1.5 py-0.5 text-[10px] font-medium text-sky-700">
                      {f.found_in}
                    </span>
                  )}
                </div>
                <p className="mt-1 font-mono text-xs text-slate-500">apiVersion: {f.api_version}</p>
                <dl className="mt-1 grid grid-cols-2 gap-x-4 text-xs text-slate-500 sm:grid-cols-3">
                  {f.deprecated_in_version && <div>Deprecated: Kubernetes {f.deprecated_in_version}</div>}
                  {f.removed_in_version && <div>Removed: Kubernetes {f.removed_in_version}</div>}
                  {f.replacement_api_version && <div>대체 API: {f.replacement_api_version}</div>}
                </dl>
                {f.notes && <p className="mt-1 text-xs text-slate-400">{f.notes}</p>}
                {f.scanned_by !== "pluto" && <SourceRefs sources={f.sources} />}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
