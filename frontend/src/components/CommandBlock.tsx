import type { UpgradeCommand } from "../types/report";

/** Section 17: 실행 명령 "제안" — 실제 실행은 하지 않는 Read-Only 표시 컴포넌트. */
export default function CommandBlock({ commands }: { commands: UpgradeCommand[] }) {
  return (
    <ul className="space-y-1.5">
      {commands.map((c, i) => (
        <li key={i}>
          <p className="text-xs text-slate-500">
            {c.description}
            {c.target ? ` (${c.target})` : ""}
          </p>
          <code className="block rounded bg-slate-900 px-2 py-1 text-xs text-emerald-300 overflow-x-auto">
            $ {c.command}
          </code>
        </li>
      ))}
    </ul>
  );
}
