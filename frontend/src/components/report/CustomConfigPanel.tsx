import type { CustomConfigArg } from "../../types/report";

const HIGH_ATTENTION_FLAGS = new Set([
  "--encryption-provider-config",
  "--audit-policy-file",
  "--audit-log-path",
  "--oidc-issuer-url",
  "--oidc-client-id",
  "--authentication-token-webhook-config-file",
  "--service-account-issuer",
]);

/** Section 4: Custom Kubernetes Component Configuration 분석 결과. */
export default function CustomConfigPanel({ configs }: { configs: CustomConfigArg[] }) {
  if (configs.length === 0) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-500 shadow-sm">
        kubeadm 기본값 외 Custom Configuration이 발견되지 않았습니다.
      </div>
    );
  }

  const byComponent = new Map<string, CustomConfigArg[]>();
  for (const c of configs) {
    byComponent.set(c.component, [...(byComponent.get(c.component) ?? []), c]);
  }

  return (
    <div className="space-y-4">
      {[...byComponent.entries()].map(([component, entries]) => (
        <div key={component} className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-800">{component}</h3>
          <p className="mt-1 text-xs text-amber-700">
            kubeadm upgrade는 이 static pod manifest를 재생성할 수 있습니다. 업그레이드 후
            아래 설정이 그대로 유지되었는지 반드시 확인하세요.
          </p>
          <div className="mt-3 space-y-2">
            {[...new Set(entries.map((e) => e.node))].map((node) => (
              <div key={node} className="rounded-lg bg-slate-50 p-3">
                <p className="text-xs font-medium text-slate-500">{node}</p>
                <ul className="mt-1 space-y-1">
                  {entries
                    .filter((e) => e.node === node)
                    .map((e, i) => (
                      <li key={i} className="flex flex-wrap items-baseline gap-1 font-mono text-xs">
                        <span className={HIGH_ATTENTION_FLAGS.has(e.flag) ? "font-bold text-red-600" : "text-slate-700"}>
                          {e.flag}
                        </span>
                        {e.value && <span className="text-slate-500">= {e.value}</span>}
                      </li>
                    ))}
                </ul>
              </div>
            ))}
          </div>
          <div className="mt-3 rounded-lg bg-slate-900 p-3 text-xs text-emerald-300">
            <p className="text-slate-400"># Upgrade 후 검증</p>
            <code className="block">$ kubectl -n kube-system get pod</code>
            <code className="block">$ cat /etc/kubernetes/manifests/{component}.yaml</code>
          </div>
        </div>
      ))}
    </div>
  );
}
