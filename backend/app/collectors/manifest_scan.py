"""Deprecated/Removed API 검사 대상 매니페스트 수집 (Section 11 확장).

두 갈래로 (kind, apiVersion) 쌍을 모은다:

1. **라이브 오브젝트** — apiVersion 변경 이력이 있거나 있을 법한 workload/네트워킹/
   정책/웹훅 kind를 대상으로 ``kubectl get`` (get/list, Read-Only RBAC 유지).
   ``kubectl api-resources`` 로 실제 존재하는 것만 골라 조회한다.
2. **미적용 Helm 차트 매니페스트** — ``helm.sh/release.v1`` Secret 의 payload
   (base64×2 + gzip JSON) 를 풀어 ``.manifest`` 에 렌더된 YAML을 꺼낸다.
   라이브에는 없지만 다음 ``helm upgrade`` 때 깨질 API를 여기서 잡는다.

수집만 하고 판정은 ``agents/deprecated_api`` + ``collectors/pluto_scan`` 이 한다.
"""

from __future__ import annotations

import base64
import gzip
import json
import logging

import yaml

from app.mcp.client import MCPClient

logger = logging.getLogger(__name__)

# api-resources 이름(그룹 포함). 이 중 클러스터에 실제 존재하는 것만 조회한다.
_LIVE_TARGET_RESOURCES = [
    "deployments.apps",
    "daemonsets.apps",
    "statefulsets.apps",
    "replicasets.apps",
    "ingresses.networking.k8s.io",
    "ingressclasses.networking.k8s.io",
    "networkpolicies.networking.k8s.io",
    "poddisruptionbudgets.policy",
    "horizontalpodautoscalers.autoscaling",
    "cronjobs.batch",
    "flowschemas.flowcontrol.apiserver.k8s.io",
    "prioritylevelconfigurations.flowcontrol.apiserver.k8s.io",
    "runtimeclasses.node.k8s.io",
    "csidrivers.storage.k8s.io",
    "csinodes.storage.k8s.io",
    "apiservices.apiregistration.k8s.io",
    "validatingwebhookconfigurations.admissionregistration.k8s.io",
    "mutatingwebhookconfigurations.admissionregistration.k8s.io",
    "customresourcedefinitions.apiextensions.k8s.io",
]


class GatheredObject(dict):
    """{apiVersion, kind, metadata, ...} 원본 + found_in 라벨."""


def gather_manifest_objects(client: MCPClient) -> list[dict]:
    """[{obj: <k8s object dict>, found_in: "live" | "helm:<release>"}] 반환."""
    gathered: list[dict] = []

    available = set(client.list_api_resource_kinds())
    targets = [r for r in _LIVE_TARGET_RESOURCES if not available or r in available]
    for obj in client.get_resources(targets):
        if obj.get("kind") and obj.get("apiVersion"):
            gathered.append({"obj": obj, "found_in": "live"})

    for rel_name, manifest in _iter_helm_manifests(client):
        for doc in _split_yaml(manifest):
            if isinstance(doc, dict) and doc.get("kind") and doc.get("apiVersion"):
                gathered.append({"obj": doc, "found_in": f"helm:{rel_name}"})

    return gathered


def to_observed(gathered: list[dict]) -> list[dict]:
    """RAG 판정기(evaluate_deprecated_apis)가 먹는 평면 형태로 변환."""
    seen: set[tuple] = set()
    observed: list[dict] = []
    for g in gathered:
        o = g["obj"]
        meta = o.get("metadata", {}) or {}
        key = (o["kind"], o["apiVersion"], meta.get("name"), meta.get("namespace"), g["found_in"])
        if key in seen:
            continue
        seen.add(key)
        observed.append(
            {
                "kind": o["kind"],
                "api_version": o["apiVersion"],
                "name": meta.get("name"),
                "namespace": meta.get("namespace"),
                "found_in": g["found_in"],
            }
        )
    return observed


def _iter_helm_manifests(client: MCPClient):
    for secret in client.get_helm_releases():
        raw = (secret.get("data") or {}).get("release")
        if not raw:
            continue
        name = (secret.get("metadata", {}).get("labels", {}) or {}).get("name") or secret.get(
            "metadata", {}
        ).get("name", "?")
        try:
            payload = json.loads(gzip.decompress(base64.b64decode(base64.b64decode(raw))))
            manifest = payload.get("manifest")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Helm 릴리스 %s payload 디코드 실패: %s", name, exc)
            continue
        if manifest:
            yield name, manifest


def _split_yaml(text: str) -> list:
    try:
        return list(yaml.safe_load_all(text))
    except yaml.YAMLError as exc:
        logger.warning("Helm 매니페스트 YAML 파싱 실패: %s", exc)
        return []
