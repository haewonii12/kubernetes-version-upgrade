export type NodeRole = "control-plane" | "worker";

export interface NodeInfo {
  name: string;
  role: NodeRole;
  os_name: string | null;
  os_version: string | null;
  kernel_version: string | null;
  architecture: string | null;
  cgroup_version: string | null;
  container_runtime: string | null;
  container_runtime_version: string | null;
  kubelet_version: string | null;
  ready: boolean;
}

export interface EtcdMember {
  name: string;
  endpoint: string;
  healthy: boolean;
  version: string | null;
}

export interface EtcdInfo {
  topology: "stacked" | "external" | "unknown";
  members: EtcdMember[];
  version: string | null;
  all_healthy: boolean;
  backup_supported: boolean;
}

export interface ControlPlaneInfo {
  node_count: number;
  is_ha: boolean;
  node_names: string[];
}

export interface CustomConfigArg {
  component: string;
  node: string;
  flag: string;
  value: string | null;
  manifest_path: string;
}

export interface SoftwareComponent {
  name: string;
  version: string | null;
  namespace: string;
  workload_kind: string;
  workload_name: string;
  image: string;
  source: string;
  confidence: string;
}

export interface CRDInfo {
  name: string;
  group: string;
  inferred_owner: string | null;
}

export interface CertExpiry {
  name: string;
  expires: string | null;
  residual_days: number | null;
  is_certificate_authority: boolean;
  observable: boolean;
  source: string | null;
}

export interface ClusterInfo {
  kubernetes_version: string;
  control_plane: ControlPlaneInfo;
  worker_node_count: number;
  nodes: NodeInfo[];
  etcd: EtcdInfo;
  cni: string | null;
  cni_version: string | null;
  csi_drivers: string[];
  ingress_controller: string | null;
  custom_configs: CustomConfigArg[];
  software_inventory: SoftwareComponent[];
  crds: CRDInfo[];
  feature_gates: Record<string, boolean>;
  helm_detected: boolean;
  certificate_expirations?: CertExpiry[];
}

export interface RAGReference {
  document: string;
  section: string | null;
  doc_id: string | null;
  excerpt: string | null;
  score: number | null;
}

export type CompatibilityStatus = "COMPATIBLE" | "INCOMPATIBLE" | "WARNING" | "UNKNOWN";

export interface CompatibilityResult {
  component: string;
  current_version: string | null;
  target_kubernetes_version: string;
  status: CompatibilityStatus;
  reason: string;
  recommendation: string | null;
  sources: RAGReference[];
}

export type RiskSeverity = "BLOCKER" | "HIGH" | "MEDIUM" | "LOW" | "INFO";

export interface RiskFinding {
  finding: string;
  severity: RiskSeverity;
  category: string;
  reason: string;
  recommendation: string;
  sources: RAGReference[];
  related_upgrade_step: string | null;
}

export interface ReadinessScore {
  score: number;
  blocker_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  info_count: number;
}

export type DeprecatedAPIStatus = "OK" | "ACTION_REQUIRED" | "UPGRADE_BLOCKER" | "UNKNOWN";

export interface DeprecatedAPIFinding {
  resource_kind: string;
  api_version: string;
  resource_name: string | null;
  namespace: string | null;
  deprecated_in_version: string | null;
  removed_in_version: string | null;
  replacement_api_version: string | null;
  status: DeprecatedAPIStatus;
  evaluated_at_target_version: string | null;
  sources: RAGReference[];
}

export interface UpgradeCommand {
  description: string;
  command: string;
  target: string | null;
}

export interface CheckItem {
  description: string;
  command: string | null;
  status: string;
}

export interface NodeUpgradeStep {
  node: string;
  order: number;
  commands: UpgradeCommand[];
  verification: string[];
}

export interface VersionUpgradePhase {
  phase_number: number;
  from_version: string;
  to_version: string;
  release_note_summary: string | null;
  release_note_summary_source: "llm" | "excerpt" | null;
  deprecated_apis: DeprecatedAPIFinding[];
  compatibility_results: CompatibilityResult[];
  pre_checks: CheckItem[];
  control_plane_steps: NodeUpgradeStep[];
  worker_steps: NodeUpgradeStep[];
  post_checks: CheckItem[];
  risks: RiskFinding[];
  sources: RAGReference[];
}

export interface UpgradePlan {
  current_version: string;
  target_version: string;
  upgrade_path: string[];
  phases: VersionUpgradePhase[];
}

export interface UpgradeReport {
  analysis_id: string;
  created_at: string;
  cluster: ClusterInfo;
  readiness: ReadinessScore;
  risks: RiskFinding[];
  upgrade_plan: UpgradePlan;
  software_compatibility: CompatibilityResult[];
  deprecated_apis: DeprecatedAPIFinding[];
  executive_summary: string | null;
}

export interface AnalysisEvent {
  stage: string;
  message: string;
  timestamp: string;
  progress: number;
}

export interface AnalysisStatus {
  analysis_id: string;
  status: "RUNNING" | "COMPLETED" | "FAILED";
  target_version: string;
  mock_mode: boolean;
  latest_event: AnalysisEvent | null;
  error: string | null;
}
