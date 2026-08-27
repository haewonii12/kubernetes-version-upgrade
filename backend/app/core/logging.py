from __future__ import annotations

import logging
import re
from pathlib import Path

_SENSITIVE_KEYS = re.compile(
    r"(token|client-key-data|client-certificate-data|password|secret|"
    r"authorization|encryption-provider-config)",
    re.IGNORECASE,
)
_MASK = "***MASKED***"


class SensitiveDataFilter(logging.Filter):
    """kubeconfig 등 민감정보가 우연히 로그에 실려도 마스킹한다 (Section 29/31)."""

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        if _SENSITIVE_KEYS.search(msg):
            record.msg = _redact(msg)
            record.args = ()
        return True


def _redact(msg: str) -> str:
    return _SENSITIVE_KEYS.sub(_MASK, msg)


def configure_logging(audit_log_path: Path | None = None) -> None:
    root = logging.getLogger()
    if root.handlers:
        return
    root.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s"))
    handler.addFilter(SensitiveDataFilter())
    root.addHandler(handler)

    if audit_log_path is not None:
        audit_log_path.parent.mkdir(parents=True, exist_ok=True)


def get_audit_logger(audit_log_path: Path) -> logging.Logger:
    audit_log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("audit")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        file_handler = logging.FileHandler(audit_log_path, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
        file_handler.addFilter(SensitiveDataFilter())
        logger.addHandler(file_handler)
        logger.propagate = False
    return logger
