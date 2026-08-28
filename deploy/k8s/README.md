# Kubernetes 배포

docker-compose 대신 이 도구(frontend + backend)를 Kubernetes 에 올린다.

```
deploy/k8s/
├── namespace.yaml     # k8s-upgrade 네임스페이스
├── backend.yaml       # Deployment(replicas=1) + Service(name: backend, :8000)
├── frontend.yaml      # Deployment(replicas=2) + Service(:80) + PDB
├── ingress.yaml       # 단일 호스트 → frontend (nginx가 / 와 /api/ 를 모두 처리)
└── kustomization.yaml
```

## 사전 준비

1. **Ingress Controller**: `ingress.yaml` 은 ingress-nginx 기준
   (`ingressClassName: nginx` + `nginx.ingress.kubernetes.io/*` 어노테이션).
   다른 컨트롤러면 아래 "다른 Ingress" 참고.
2. **이미지**: `k8s-upgrade-backend:latest`, `k8s-upgrade-frontend:latest`
   (`docker/export-images-podman.sh` 산출물). 둘 중 하나:
   - **사내 레지스트리에 push** (권장): `podman load` 후 retag/push →
     `kustomization.yaml` 의 `images:` 블록으로 이름/태그 지정.
   - **각 노드에 직접 import**: 모든 워커 노드에서
     `ctr -n k8s.io images import <(gunzip -c k8s-upgrade-images.tar.gz)` →
     `backend.yaml`/`frontend.yaml` 의 `imagePullPolicy` 를 `Never` 로 바꾸고,
     스케줄 노드를 `nodeSelector` 로 고정.

## 배포

```bash
# ingress.yaml 의 host 를 실제 도메인으로 수정한 뒤
kubectl apply -k deploy/k8s/

kubectl -n k8s-upgrade get pods,svc,ingress
```

접속: `http://<ingress-host>/` (mock 모드로 바로 체험 가능).

## 알아둘 것

| 항목 | 설명 |
|---|---|
| **backend replicas=1** | 분석 세션(SSE 진행 + 결과)이 프로세스 메모리에 있다. 늘리면 진행 폴링/리포트 조회가 다른 pod로 가서 깨진다. |
| **Service 이름 `backend`** | frontend 이미지의 `nginx.conf` 가 `http://backend:8000` 를 하드코딩. 바꾸려면 프론트 이미지 재빌드. |
| **RAG 문서** | 이미지에 `COPY` 되어 있다(`/app/rag/documents`). 문서를 고치려면 백엔드 이미지 재빌드. 자주 고치면 ConfigMap/PVC + `UPGRADE_AGENT_RAG_DOCUMENTS_DIR` 로 분리. |
| **스냅샷/audit 로그** | `emptyDir` (`/app/backend/var`) — pod 재시작 시 사라짐. 유지하려면 PVC 로 교체(replicas=1 이라 RWO 로 충분). |
| **kubectl-ai / pluto** | 백엔드 이미지에 구워져 있음. real 모드 분석 시 추가 다운로드 없음. |
| **real 모드 분석** | 업로드한 read-only kubeconfig 로 대상 클러스터 API 서버에 접근. 백엔드 pod 가 그 API 서버로 **egress** 가능해야 한다(NetworkPolicy/방화벽). RBAC 예시: `docker/mcp/rbac.yaml`. |
| **CORS** | SPA와 API가 같은 ingress 호스트라 same-origin → CORS 미발생. `UPGRADE_AGENT_CORS_ALLOW_ORIGINS` 는 backend를 따로 노출할 때만. |

## SSE (진행률 스트리밍)

`/api/v1/analysis/{id}/events` 는 Server-Sent Events. 경로상 버퍼링을 다 꺼야 한다:
- ingress: `ingress.yaml` 의 `proxy-buffering: "off"` + 긴 timeout (설정됨)
- frontend nginx: `docker/frontend/nginx.conf` 의 `proxy_buffering off` (이미 설정됨)

## 다른 Ingress

- **Traefik**: `ingressClassName: traefik`, 어노테이션 제거, SSE는 Traefik이 기본으로 스트리밍.
- **Gateway API**: `HTTPRoute` 로 `k8s-upgrade.example.com` → `frontend:80` 단일 라우트.
- **Ingress 없이**: `frontend` Service 를 `type: LoadBalancer` 또는 `NodePort` 로.

## TLS

`ingress.yaml` 의 `tls:` 블록 주석 해제 + `k8s-upgrade-tls` Secret 생성
(cert-manager `Certificate` 또는 `kubectl create secret tls`).
