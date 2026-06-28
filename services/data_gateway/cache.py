import json
import time
from pathlib import Path
from typing import Any, Optional


class FileCache:
    """TTL-keyed JSON file cache stored under cache_dir."""

    def __init__(self, cache_dir: Path, ttl_seconds: int = 3600) -> None:
        self._dir = cache_dir
        self._ttl = ttl_seconds
        self._dir.mkdir(parents=True, exist_ok=True)

    def _key_path(self, key: str) -> Path:
        safe = key.replace("/", "_").replace(":", "_").replace(" ", "_")
        return self._dir / f"{safe}.json"

    def get(self, key: str) -> Optional[Any]:
        path = self._key_path(key)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        if time.time() - payload["stored_at"] > self._ttl:
            path.unlink(missing_ok=True)
            return None
        return payload["data"]

    def set(self, key: str, data: Any) -> None:
        path = self._key_path(key)
        payload = {"stored_at": time.time(), "data": data}
        path.write_text(json.dumps(payload, ensure_ascii=False, default=str), encoding="utf-8")

    def invalidate(self, key: str) -> None:
        self._key_path(key).unlink(missing_ok=True)
