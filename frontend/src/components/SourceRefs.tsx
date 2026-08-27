import type { RAGReference } from "../types/report";

/** Section 24: RAG 근거 표시 — 모든 판단에는 가능한 경우 Reference를 표시한다. */
export default function SourceRefs({ sources }: { sources: RAGReference[] }) {
  if (!sources || sources.length === 0) {
    return <p className="text-xs text-slate-400">근거 문서 없음 (Manual Verification Required)</p>;
  }
  return (
    <div className="mt-1 space-y-1">
      <p className="text-xs font-semibold text-slate-500">Source</p>
      <ul className="space-y-0.5">
        {sources.map((s, i) => (
          <li key={i} className="text-xs text-slate-500">
            {s.document}
            {s.section ? ` — ${s.section}` : ""}
          </li>
        ))}
      </ul>
    </div>
  );
}
