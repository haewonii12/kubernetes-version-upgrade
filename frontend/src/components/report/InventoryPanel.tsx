import type { ClusterInfo } from "../../types/report";

/** Section 20: Cluster Inventory UI. */
export default function InventoryPanel({ cluster }: { cluster: ClusterInfo }) {
  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-sm font-semibold text-slate-500">Cluster Inventory</h3>
        <dl className="mt-4 grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
          <Item term="Kubernetes" desc={cluster.kubernetes_version} />
          <Item term="Control Plane" desc={`${cluster.control_plane.node_count}`} />
          <Item term="Worker" desc={`${cluster.worker_node_count}`} />
          <Item term="HA" desc={cluster.control_plane.is_ha ? "YES" : "NO"} />
          <Item term="etcd" desc={cluster.etcd.topology} />
          <Item term="CNI" desc={cluster.cni ? `${cluster.cni} ${cluster.cni_version ?? ""}` : "미확인"} />
          <Item term="Ingress" desc={cluster.ingress_controller ?? "미확인"} />
          <Item term="Helm 사용" desc={cluster.helm_detected ? "YES" : "NO"} />
        </dl>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-sm font-semibold text-slate-500">Node 목록</h3>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-xs uppercase text-slate-400">
                <th className="py-2 pr-4">Node</th>
                <th className="py-2 pr-4">Role</th>
                <th className="py-2 pr-4">OS</th>
                <th className="py-2 pr-4">Kernel</th>
                <th className="py-2 pr-4">cgroup</th>
                <th className="py-2 pr-4">Container Runtime</th>
                <th className="py-2 pr-4">kubelet</th>
              </tr>
            </thead>
            <tbody>
              {cluster.nodes.map((n) => (
                <tr key={n.name} className="border-b border-slate-100">
                  <td className="py-2 pr-4 font-medium text-slate-800">{n.name}</td>
                  <td className="py-2 pr-4">{n.role}</td>
                  <td className="py-2 pr-4">
                    {n.os_name} {n.os_version}
                  </td>
                  <td className="py-2 pr-4 text-xs text-slate-500">{n.kernel_version}</td>
                  <td className="py-2 pr-4">{n.cgroup_version ?? "-"}</td>
                  <td className="py-2 pr-4">
                    {n.container_runtime} {n.container_runtime_version}
                  </td>
                  <td className="py-2 pr-4">{n.kubelet_version}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-sm font-semibold text-slate-500">etcd</h3>
        <dl className="mt-3 grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
          <Item term="Topology" desc={cluster.etcd.topology} />
          <Item term="Members" desc={`${cluster.etcd.members.length}`} />
          <Item term="Health" desc={cluster.etcd.all_healthy ? "Healthy" : "확인 필요"} />
          <Item term="Version" desc={cluster.etcd.version ?? "미확인"} />
        </dl>
        <ul className="mt-3 space-y-1 text-xs text-slate-500">
          {cluster.etcd.members.map((m) => (
            <li key={m.name}>
              {m.name} — {m.endpoint} ({m.healthy ? "Ready" : "Not Ready"}, v{m.version})
            </li>
          ))}
        </ul>
      </div>

      {cluster.crds.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-500">CRD ({cluster.crds.length}개)</h3>
          <div className="mt-3 flex flex-wrap gap-2">
            {cluster.crds.map((c) => (
              <span key={c.name} className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700">
                {c.name}
                {c.inferred_owner ? ` · ${c.inferred_owner}` : ""}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Item({ term, desc }: { term: string; desc: string }) {
  return (
    <div>
      <dt className="text-xs text-slate-400">{term}</dt>
      <dd className="font-medium text-slate-800">{desc}</dd>
    </div>
  );
}
