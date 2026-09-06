import hmac
import os
from pathlib import Path

from fastapi import Header, HTTPException


def require_api_key(x_codegrok_key: str | None = Header(default=None)) -> None:
    expected = os.getenv("CODEGROK_API_KEY")
    if not expected:
        raise HTTPException(status_code=503, detail="CODEGROK_API_KEY is not configured")
    if not x_codegrok_key or not hmac.compare_digest(x_codegrok_key, expected):
        raise HTTPException(status_code=401, detail="Invalid CodeGrok API key")


def validate_allowed_path(path: Path) -> Path:
    allowed_roots = [
        Path(value).expanduser().resolve()
        for value in os.getenv("CODEGROK_ALLOWED_ROOTS", "").split(os.pathsep)
        if value.strip()
    ]
    resolved_path = path.expanduser().resolve()
    if not allowed_roots:
        raise HTTPException(status_code=503, detail="CODEGROK_ALLOWED_ROOTS is not configured")
    if not any(resolved_path == root or root in resolved_path.parents for root in allowed_roots):
        raise HTTPException(status_code=403, detail="Repository path is outside the configured allowed roots")
    return resolved_path