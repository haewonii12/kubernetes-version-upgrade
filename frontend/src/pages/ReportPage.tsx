import { useState } from "react";
import type { UpgradeReport } from "../types/report";
import OverviewPanel from "../components/report/OverviewPanel";
import InventoryPanel from "../components/report/InventoryPanel";
import SoftwarePanel from "../components/report/SoftwarePanel";
import DeprecatedApiPanel from "../components/report/DeprecatedApiPanel";
import CustomConfigPanel from "../components/report/CustomConfigPanel";
import RiskPanel from "../components/report/RiskPanel";
import TimelinePanel from "../components/report/TimelinePanel";

const TABS = [
  { key: "overview", label: "개요" },
  { key: "inventory", label: "Cluster Inventory" },
  { key: "software", label: "설치된 소프트웨어" },
  { key: "deprecated", label: "Deprecated API" },
  { key: "custom-config", label: "Custom Configuration" },
  { key: "risk", label: "Risk" },
  { key: "timeline", label: "Upgrade Timeline" },
] as const;

type TabKey = (typeof TABS)[number]["key"];

interface Props {
  report: UpgradeReport;
  onReset: () => void;
}

export default function ReportPage({ report, onReset }: Props) {
  const [tab, setTab] = useState<TabKey>("overview");

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-900">Upgrade Report</h2>
        <button onClick={onReset} className="text-sm text-slate-500 hover:text-slate-800">
          새 분석 시작
        </button>
      </div>

      <div className="mb-6 flex flex-wrap gap-1 border-b border-slate-200">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`rounded-t-md px-4 py-2 text-sm font-medium ${
              tab === t.key ? "border-b-2 border-slate-900 text-slate-900" : "text-slate-500 hover:text-slate-800"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "overview" && <OverviewPanel report={report} />}
      {tab === "inventory" && <InventoryPanel cluster={report.cluster} />}
      {tab === "software" && <SoftwarePanel cluster={report.cluster} compatibility={report.software_compatibility} />}
      {tab === "deprecated" && (
        <DeprecatedApiPanel
          findings={report.deprecated_apis}
          plutoSkipped={report.deprecated_api_pluto_skipped}
        />
      )}
      {tab === "custom-config" && <CustomConfigPanel configs={report.cluster.custom_configs} />}
      {tab === "risk" && <RiskPanel risks={report.risks} readiness={report.readiness} />}
      {tab === "timeline" && <TimelinePanel phases={report.upgrade_plan.phases} />}
    </div>
  );
}
