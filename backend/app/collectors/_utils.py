"""Collector 모듈들이 공유하는 순수 파싱 helper (DRY)."""

from __future__ import annotations

from typing import Any


def container_args(pod: dict[str, Any], name_contains: str) -> list[str]:
    containers = pod.get("spec", {}).get("containers", [])
    for c in containers:
        if name_contains in c.get("name", ""):
            return list(c.get("command", [])) + list(c.get("args", []))
    if containers:
        c = containers[0]
        return list(c.get("command", [])) + list(c.get("args", []))
    return []


def extract_flag(args: list[str], flag: str) -> str | None:
    for idx, a in enumerate(args):
        if a == flag and idx + 1 < len(args):
            return args[idx + 1]
        if a.startswith(flag + "="):
            return a.split("=", 1)[1]
    return None


def pod_ready(pod: dict[str, Any]) -> bool:
    if pod.get("status", {}).get("phase") != "Running":
        return False
    conditions = pod.get("status", {}).get("conditions", [])
    return any(c.get("type") == "Ready" and c.get("status") == "True" for c in conditions)


def is_control_plane_node(node: dict[str, Any]) -> bool:
    labels = node.get("metadata", {}).get("labels", {})
    return "node-role.kubernetes.io/control-plane" in labels or "node-role.kubernetes.io/master" in labels
