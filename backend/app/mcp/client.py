"""kubectl-ai MCP Server 클라이언트.

Collector 계층은 이 모듈이 노출하는 ``MCPClient`` 인터페이스만 알고 있으며,
실제로 Real Cluster에 붙는지(``RealMCPClient``) Mock Fixture를 읽는지
(``MockMCPClient``) 는 신경 쓰지 않는다 (Strategy 패턴, DRY).

RBAC/실행 제약 (Section 30):
    - 여기서 노출하는 모든 메서드는 kubectl 의 ``get``/``list`` 에 대응한다.
    - ``exec``, ``create``, ``patch``, ``delete`` 에 해당하는 메서드는 의도적으로
      제공하지 않는다. 즉 etcd 실제 endpoint health(``etcdctl endpoint health``)나
      cgroup 버전 확인처럼 원래 노드 exec/bash 가 필요한 정보는, mirror pod spec 등
      get/list 로 얻을 수 있는 간접 증거로 "best-effort" 추론하고, 불가능하면
      명시적으로 ``None`` / manual-check 필요로 표시한다.
"""

from __future__ import annotations

import abc
import json
import logging
import queue
import re
import shlex
import threading
from concurrent.futures import Future
from concurrent.futures import TimeoutError as FutureTimeoutError
from pathlib import Path
from typing import Any

import anyio

logger = logging.getLogger(__name__)

# kubectl-ai MCP 세션 연결(initialize)에 허용하는 최대 시간.
_CONNECT_TIMEOUT_SECONDS = 20.0
# 개별 kubectl tool 호출(get/list/watch)에 허용하는 최대 시간.
_CALL_TIMEOUT_SECONDS = 30.0

# kubectl-ai(>=0.0.31)의 내장 "kubectl" tool 응답 형식:
#   Command: "kubectl ..."\nError: "..."\nStdout: "..."\nStderr: "..."\nExitCode: 0\nStreamType: "..."}
# (Go의 %q 포맷 — 값은 각각 큰따옴표로 감싼 이스케이프 문자열이다. Stdout 안의
# 실제 kubectl 출력(JSON)을 꺼내려면 이 wrapper를 한 번 벗겨내야 한다. 필드 순서가
# 고정되어 있으므로 각 필드는 그 다음 필드 이름을 경계로 삼아 lazy 매칭한다 —
# JSON 내용 안의 따옴표는 항상 ``\"``로 escape되어 있어 이 경계와 혼동되지 않는다.)
_STDOUT_RE = re.compile(r'Stdout: "(.*?)"\nStderr: ', re.DOTALL)
_ERROR_RE = re.compile(r'Error: "(.*?)"\nStdout: ', re.DOTALL)


def _unescape_go_quoted_string(escaped: str) -> str:
    """Go의 %q 로 escape된 문자열 내용을 원래 문자열로 되돌린다.

    Go의 double-quoted string escape 규칙은 JSON 문자열 escape 규칙과 사실상
    호환되므로, 앞뒤에 큰따옴표를 붙여 JSON 문자열 리터럴로 다시 파싱한다.
    """
    return json.loads(f'"{escaped}"')


def _parse_kubectl_tool_result(text: str) -> Any:
    error_match = _ERROR_RE.search(text)
    if error_match:
        error_text = _unescape_go_quoted_string(error_match.group(1)).strip()
        if error_text:
            raise RuntimeError(f"kubectl 명령 실행 중 오류가 발생했습니다: {error_text}")

    stdout_match = _STDOUT_RE.search(text)
    if not stdout_match:
        raise RuntimeError(f"kubectl-ai 응답 형식을 해석할 수 없습니다: {text[:300]!r}")

    raw_stdout = _unescape_go_quoted_string(stdout_match.group(1))
    return json.loads(raw_stdout) if raw_stdout.strip() else {}


class MCPClient(abc.ABC):
    """kubectl-ai MCP Server 가 노출하는 Read-Only 조회 기능의 추상 인터페이스."""

    @abc.abstractmethod
    def get_version(self) -> dict[str, Any]: ...

    @abc.abstractmethod
    def get_nodes(self) -> list[dict[str, Any]]: ...

    @abc.abstractmethod
    def get_namespaces(self) -> list[str]: ...

    @abc.abstractmethod
    def get_pods(self, namespace: str | None = None) -> list[dict[str, Any]]: ...

    @abc.abstractmethod
    def get_deployments(self, namespace: str | None = None) -> list[dict[str, Any]]: ...

    @abc.abstractmethod
    def get_daemonsets(self, namespace: str | None = None) -> list[dict[str, Any]]: ...

    @abc.abstractmethod
    def get_statefulsets(self, namespace: str | None = None) -> list[dict[str, Any]]: ...

    @abc.abstractmethod
    def get_crds(self) -> list[dict[str, Any]]: ...

    @abc.abstractmethod
    def get_api_services(self) -> list[dict[str, Any]]: ...

    @abc.abstractmethod
    def get_storage_classes(self) -> list[dict[str, Any]]: ...

    @abc.abstractmethod
    def get_persistent_volumes(self) -> list[dict[str, Any]]: ...

    @abc.abstractmethod
    def get_helm_releases(self) -> list[dict[str, Any]]: ...

    @abc.abstractmethod
    def get_horizontal_pod_autoscalers(self) -> list[dict[str, Any]]: ...

    @abc.abstractmethod
    def get_pod_disruption_budgets(self) -> list[dict[str, Any]]: ...

    @abc.abstractmethod
    def get_flow_control_configs(self) -> list[dict[str, Any]]: ...

    def close(self) -> None:
        """리소스 정리 (기본은 no-op). 세션/subprocess를 여는 구현체는 override 한다."""
        return None


class RealMCPClient(MCPClient):
    """실제 kubectl-ai MCP Server(stdio)에 연결하는 구현체.

    MCP 표준 SDK(``mcp`` 패키지)의 ``ClientSession`` 을 사용해 kubectl-ai가 노출하는
    ``kubectl`` 도구를 read-only 인자로만 호출한다. kubectl-ai MCP 서버 자체의
    RBAC는 서버 기동 시 ServiceAccount에 get/list/watch ClusterRole만 bind 하는
    것으로 강제한다 (docker/mcp/rbac.yaml 참고).

    구현 메모: ``mcp`` SDK의 stdio transport는 subprocess의 stdin/stdout을
    세션의 in-memory stream으로 이어주는 백그라운드 pipe-bridging task를
    내부적으로 띄우며, 이 task는 세션을 연 ``async with`` 블록(=단일 이벤트 루프)이
    살아있는 동안만 유효하다. 따라서 이 클라이언트는 생성 시 전용 백그라운드
    스레드를 하나 띄우고 그 스레드의 이벤트 루프 안에서 세션을 "단 한 번" 열어
    클라이언트 생존 기간 내내 유지하며, 동기 API인 ``_call_kubectl`` 은
    thread-safe 큐로 요청을 넘기고 결과를 기다리는 방식으로 동작한다
    (호출마다 새 이벤트 루프를 만들어 캐시된 세션을 재사용하면, 이전 루프와
    함께 죽은 pipe-bridging task에 묶인 스트림을 쓰게 되어 응답이 영원히
    오지 않는다 — 최초 이 클래스를 그렇게 구현했다가 Real 모드 분석이 "클러스터
    연결" 단계에서 무한정 멈추는 버그로 이어진 적이 있다).

    연결(initialize)과 각 tool 호출 모두 timeout이 걸려 있어, kubectl-ai가
    응답하지 않아도 무한 대기 대신 명확한 예외로 끝난다.
    """

    def __init__(self, command: str, args: list[str], env: dict[str, str] | None = None) -> None:
        self._command = command
        self._args = args
        self._env = env
        self._request_q: queue.Queue[tuple[list[str], Future] | None] = queue.Queue()
        self._ready = threading.Event()
        self._connect_error: BaseException | None = None
        self._thread = threading.Thread(target=self._run_loop, name="mcp-client-loop", daemon=True)
        self._thread.start()

        if not self._ready.wait(timeout=_CONNECT_TIMEOUT_SECONDS + 5):
            raise TimeoutError(
                f"kubectl-ai MCP 서버 연결이 {_CONNECT_TIMEOUT_SECONDS:.0f}초 내에 "
                "완료되지 않았습니다. kubectl-ai 프로세스, kubeconfig 권한을 확인하세요."
            )
        if self._connect_error is not None:
            raise self._connect_error

    def _run_loop(self) -> None:
        try:
            anyio.run(self._loop_main)
        except Exception as exc:  # noqa: BLE001
            if not self._ready.is_set():
                self._connect_error = exc
                self._ready.set()
            else:
                logger.exception("MCP client 백그라운드 루프가 예기치 않게 종료되었습니다")

    async def _loop_main(self) -> None:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        params = StdioServerParameters(command=self._command, args=self._args, env=self._env)
        try:
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    with anyio.fail_after(_CONNECT_TIMEOUT_SECONDS):
                        await session.initialize()
                    self._ready.set()

                    while True:
                        item = await anyio.to_thread.run_sync(self._request_q.get)
                        if item is None:  # close() 신호
                            return
                        args, future = item
                        try:
                            command = "kubectl " + shlex.join(args)
                            with anyio.fail_after(_CALL_TIMEOUT_SECONDS):
                                result = await session.call_tool(
                                    "kubectl", {"command": command, "modifies_resource": "no"}
                                )
                            text = "".join(block.text for block in result.content if hasattr(block, "text"))
                            if result.is_error:
                                raise RuntimeError(f"kubectl-ai MCP tool 오류: {text[:300]}")
                            future.set_result(_parse_kubectl_tool_result(text))
                        except Exception as exc:  # noqa: BLE001
                            future.set_exception(exc)
        except Exception as exc:
            if not self._ready.is_set():
                self._connect_error = exc
                self._ready.set()
            raise

    def _call_kubectl(self, args: list[str]) -> dict[str, Any] | list[Any]:
        future: Future = Future()
        self._request_q.put((args, future))
        try:
            return future.result(timeout=_CALL_TIMEOUT_SECONDS + 5)
        except FutureTimeoutError as exc:
            raise TimeoutError(
                f"kubectl-ai 응답이 {_CALL_TIMEOUT_SECONDS:.0f}초 내에 도착하지 않았습니다: "
                f"kubectl {' '.join(args)}"
            ) from exc

    def close(self) -> None:
        self._request_q.put(None)
        self._thread.join(timeout=_CONNECT_TIMEOUT_SECONDS)
        if self._thread.is_alive():
            logger.warning("MCP client 백그라운드 스레드가 정상 종료되지 않았습니다")

    def get_version(self) -> dict[str, Any]:
        return self._call_kubectl(["version", "-o", "json"])  # type: ignore[return-value]

    def get_nodes(self) -> list[dict[str, Any]]:
        return self._call_kubectl(["get", "nodes", "-o", "json"]).get("items", [])  # type: ignore

    def get_namespaces(self) -> list[str]:
        items = self._call_kubectl(["get", "namespaces", "-o", "json"]).get("items", [])  # type: ignore
        return [i["metadata"]["name"] for i in items]

    def _get_all_ns(self, kind: str, namespace: str | None) -> list[dict[str, Any]]:
        args = ["get", kind, "-o", "json"]
        args += ["-n", namespace] if namespace else ["-A"]
        return self._call_kubectl(args).get("items", [])  # type: ignore

    def get_pods(self, namespace: str | None = None) -> list[dict[str, Any]]:
        return self._get_all_ns("pods", namespace)

    def get_deployments(self, namespace: str | None = None) -> list[dict[str, Any]]:
        return self._get_all_ns("deployments", namespace)

    def get_daemonsets(self, namespace: str | None = None) -> list[dict[str, Any]]:
        return self._get_all_ns("daemonsets", namespace)

    def get_statefulsets(self, namespace: str | None = None) -> list[dict[str, Any]]:
        return self._get_all_ns("statefulsets", namespace)

    def get_crds(self) -> list[dict[str, Any]]:
        return self._call_kubectl(["get", "crd", "-o", "json"]).get("items", [])  # type: ignore

    def get_api_services(self) -> list[dict[str, Any]]:
        return self._call_kubectl(["get", "apiservices", "-o", "json"]).get("items", [])  # type: ignore

    def get_storage_classes(self) -> list[dict[str, Any]]:
        return self._call_kubectl(["get", "storageclasses", "-o", "json"]).get("items", [])  # type: ignore

    def get_persistent_volumes(self) -> list[dict[str, Any]]:
        return self._call_kubectl(["get", "pv", "-o", "json"]).get("items", [])  # type: ignore

    def get_helm_releases(self) -> list[dict[str, Any]]:
        # Helm release는 Secret(type=helm.sh/release.v1)으로 저장된다 (get만 사용).
        return self._call_kubectl(
            ["get", "secrets", "-A", "--field-selector", "type=helm.sh/release.v1", "-o", "json"]
        ).get("items", [])  # type: ignore

    def get_horizontal_pod_autoscalers(self) -> list[dict[str, Any]]:
        return self._get_all_ns("hpa", None)

    def get_pod_disruption_budgets(self) -> list[dict[str, Any]]:
        return self._get_all_ns("pdb", None)

    def get_flow_control_configs(self) -> list[dict[str, Any]]:
        return self._call_kubectl(["get", "flowschemas", "-o", "json"]).get("items", [])  # type: ignore


class MockMCPClient(MCPClient):
    """examples/mock-cluster/*.json fixture 를 읽어 동일 인터페이스로 응답한다.

    실제 Kubernetes 클러스터 없이 전체 Agent 파이프라인(수집→분석→RAG→
    Compatibility→Risk→Plan)을 End-to-End 로 검증하기 위한 구현체.
    """

    def __init__(self, fixture_dir: Path) -> None:
        self._dir = fixture_dir
        self._cache: dict[str, Any] = {}

    def _load(self, name: str) -> Any:
        if name not in self._cache:
            path = self._dir / f"{name}.json"
            if not path.exists():
                logger.warning("mock fixture missing: %s", path)
                self._cache[name] = [] if name != "version" else {}
            else:
                self._cache[name] = json.loads(path.read_text(encoding="utf-8"))
        return self._cache[name]

    def get_version(self) -> dict[str, Any]:
        return self._load("version")

    def get_nodes(self) -> list[dict[str, Any]]:
        return self._load("nodes").get("items", [])

    def get_namespaces(self) -> list[str]:
        return [i["metadata"]["name"] for i in self._load("namespaces").get("items", [])]

    def get_pods(self, namespace: str | None = None) -> list[dict[str, Any]]:
        items = self._load("pods").get("items", [])
        if namespace:
            return [p for p in items if p["metadata"]["namespace"] == namespace]
        return items

    def get_deployments(self, namespace: str | None = None) -> list[dict[str, Any]]:
        items = self._load("deployments").get("items", [])
        if namespace:
            return [d for d in items if d["metadata"]["namespace"] == namespace]
        return items

    def get_daemonsets(self, namespace: str | None = None) -> list[dict[str, Any]]:
        items = self._load("daemonsets").get("items", [])
        if namespace:
            return [d for d in items if d["metadata"]["namespace"] == namespace]
        return items

    def get_statefulsets(self, namespace: str | None = None) -> list[dict[str, Any]]:
        items = self._load("statefulsets").get("items", [])
        if namespace:
            return [d for d in items if d["metadata"]["namespace"] == namespace]
        return items

    def get_crds(self) -> list[dict[str, Any]]:
        return self._load("crds").get("items", [])

    def get_api_services(self) -> list[dict[str, Any]]:
        return self._load("apiservices").get("items", [])

    def get_storage_classes(self) -> list[dict[str, Any]]:
        return self._load("storageclasses").get("items", [])

    def get_persistent_volumes(self) -> list[dict[str, Any]]:
        return self._load("persistentvolumes").get("items", [])

    def get_helm_releases(self) -> list[dict[str, Any]]:
        return self._load("helm_releases").get("items", [])

    def get_horizontal_pod_autoscalers(self) -> list[dict[str, Any]]:
        return self._load("hpas").get("items", [])

    def get_pod_disruption_budgets(self) -> list[dict[str, Any]]:
        return self._load("pdbs").get("items", [])

    def get_flow_control_configs(self) -> list[dict[str, Any]]:
        return self._load("flowschemas").get("items", [])


def create_mcp_client(
    mode: str,
    *,
    fixture_dir: Path | None = None,
    server_command: str = "kubectl-ai",
    server_args: list[str] | None = None,
    kubeconfig_path: Path | None = None,
) -> MCPClient:
    if mode == "mock":
        assert fixture_dir is not None, "mock 모드에는 fixture_dir 이 필요합니다"
        return MockMCPClient(fixture_dir)
    if mode == "stdio":
        env = {"KUBECONFIG": str(kubeconfig_path)} if kubeconfig_path else None
        return RealMCPClient(server_command, server_args or [], env=env)
    raise ValueError(f"알 수 없는 MCP mode: {mode}")
