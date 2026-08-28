#!/usr/bin/env bash
# 폐쇄망의 각 노드(Control Plane / Worker)에서 root로 실행.
# 번들 tarball을 푼 디렉터리 안에서 실행하면:
#   1) artifacts/rpms 를 file:// 로컬 dnf 저장소로 등록
#   2) artifacts/images/*.tar 를 containerd(k8s.io namespace)로 import
#
#   sudo bash load.sh            # RPM 저장소 + 이미지 전부
#   sudo bash load.sh images     # 이미지만
#   sudo bash load.sh rpms       # RPM 저장소만
#
# 이 스크립트는 업그레이드를 수행하지 않는다 — 아티팩트만 각 노드에 올린다.
# 실제 순서(kubeadm upgrade apply / node, drain/uncordon)는 README 참고.
set -euo pipefail
cd "$(dirname "$0")"
ART="artifacts"
REPO_DIR="/opt/k8s-upgrade-bundle/rpms"
CTR="${CTR:-$(command -v ctr || true)}"

load_rpms() {
  echo ">> RPM 로컬 저장소 구성: $REPO_DIR"
  mkdir -p "$REPO_DIR"
  cp -f "$ART"/rpms/*/*.rpm "$REPO_DIR"/
  if command -v createrepo_c >/dev/null; then createrepo_c "$REPO_DIR"
  elif command -v createrepo   >/dev/null; then createrepo   "$REPO_DIR"
  else
    echo "   createrepo(_c) 없음 — repo 메타데이터 없이 개별 설치만 가능."
    echo "   예:  dnf install -y $REPO_DIR/kubeadm-1.33.13-*.rpm $REPO_DIR/kubelet-1.33.13-*.rpm $REPO_DIR/kubectl-1.33.13-*.rpm"
    return
  fi
  cat > /etc/yum.repos.d/k8s-upgrade-bundle.repo <<EOF
[k8s-upgrade-bundle]
name=Kubernetes upgrade bundle (offline, 1.33-1.36)
baseurl=file://$REPO_DIR
enabled=1
gpgcheck=0
EOF
  echo "   완료. 사용 예 (한 minor씩):"
  echo "     dnf install -y kubeadm-1.33.13 kubelet-1.33.13 kubectl-1.33.13 --disablerepo='*' --enablerepo=k8s-upgrade-bundle"
}

load_images() {
  [ -n "$CTR" ] || { echo "!! ctr 없음 — containerd CLI 필요"; exit 1; }
  echo ">> containerd(k8s.io)로 이미지 import"
  for t in "$ART"/images/*.tar; do
    [ -e "$t" ] || { echo "   이미지 tar 없음"; break; }
    echo "   import $t"
    "$CTR" -n k8s.io images import "$t"
  done
  echo "   확인:  ctr -n k8s.io images ls | grep -E 'kube-|etcd|coredns|pause'"
}

case "${1:-all}" in
  rpms)   load_rpms ;;
  images) load_images ;;
  all|"") load_rpms; echo; load_images ;;
  *) echo "usage: $0 [rpms|images]"; exit 1 ;;
esac
