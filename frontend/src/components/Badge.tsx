const SEVERITY_STYLE: Record<string, string> = {
  BLOCKER: "bg-red-600 text-white",
  HIGH: "bg-orange-500 text-white",
  MEDIUM: "bg-amber-400 text-amber-950",
  LOW: "bg-sky-200 text-sky-900",
  INFO: "bg-slate-200 text-slate-700",
  COMPATIBLE: "bg-emerald-500 text-white",
  INCOMPATIBLE: "bg-red-600 text-white",
  WARNING: "bg-amber-400 text-amber-950",
  UNKNOWN: "bg-slate-300 text-slate-800",
  OK: "bg-emerald-500 text-white",
  ACTION_REQUIRED: "bg-orange-500 text-white",
  UPGRADE_BLOCKER: "bg-red-600 text-white",
};

export default function Badge({ label }: { label: string }) {
  const style = SEVERITY_STYLE[label] ?? "bg-slate-200 text-slate-800";
  return <span className={`badge ${style}`}>{label}</span>;
}
