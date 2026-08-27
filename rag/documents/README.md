# RAG 문서 저장소

이 디렉토리의 문서가 Kubernetes Upgrade Agent의 모든 Compatibility/Risk 판단 근거입니다.
**코드에는 어떤 버전 조합이 호환되는지에 대한 규칙이 하드코딩되어 있지 않습니다** —
Agent는 오직 이 문서들을 검색한 결과만으로 판단하며, 근거가 없으면 `UNKNOWN`
(Manual Verification Required)으로 표시합니다.

> **중요**: 이 저장소에 포함된 문서는 PoC/데모 목적의 **샘플 데이터**입니다.
> 실제 운영 클러스터에 적용하기 전에 각 컴포넌트의 공식 Release Note /
> Compatibility Matrix로 반드시 교체하십시오.

## 문서 추가 방법

1. `release-notes/`, `deprecation-guides/`, `kubeadm-guides/`, `compatibility-matrix/`
   중 알맞은 하위 폴더에 `.md` 파일을 추가합니다 (새 하위 폴더를 만들어도 됩니다 —
   `rglob("*.md")`로 재귀 탐색하므로 위치는 자유롭습니다).
2. 파일 상단에 frontmatter를 작성합니다.

   ```markdown
   ---
   doc_id: calico-compatibility-matrix
   title: Calico Compatibility Matrix
   doc_type: compatibility_matrix
   component: calico
   applies_to_k8s: ["1.33", "1.34", "1.35", "1.36"]
   tags: [cni, calico]
   ---
   ```

3. 본문은 `## 섹션 제목` 단위로 나눠 작성하면 검색 결과에 섹션명이 함께 표시됩니다.
4. Compatibility 판정이 필요한 문서는 본문 어딘가에 다음 형식의 코드 블록을 추가합니다
   (자유 텍스트만으로는 Agent가 자동으로 COMPATIBLE/WARNING을 판정하지 않습니다 —
   구조화된 판정 근거가 있어야 합니다):

   ```yaml
   compatibility_matrix:
     component: calico
     current_version_pattern: "3.30"   # 생략 시 모든 현재 버전에 적용
     entries:
       - target_kubernetes_minor: "1.36"
         status: WARNING   # COMPATIBLE | INCOMPATIBLE | WARNING
         reason: "..."
         recommendation: "..."
   ```

5. Deprecated/Removed API 문서는 다음 형식을 사용합니다.

   ```yaml
   deprecated_api_guide:
     entries:
       - kind: FlowSchema
         api_version: flowcontrol.apiserver.k8s.io/v1beta3
         deprecated_in_version: "1.33"
         removed_in_version: "1.35"
         replacement_api_version: flowcontrol.apiserver.k8s.io/v1
         notes: "..."
   ```

6. (선택) `cd rag/ingestion && python3 build_index.py` 로 frontmatter/YAML 문법
   오류가 없는지 미리 검증할 수 있습니다. 백엔드 서버는 기동 시 이 디렉토리를
   항상 새로 파싱하므로 별도 재시작 외 추가 작업은 필요 없습니다.

`README.md` 파일 자체는 색인 대상에서 제외됩니다.
