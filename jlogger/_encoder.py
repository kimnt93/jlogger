import json
from typing import Any, Dict, Mapping, Optional

try:
    from ._native import dumps, format_record
except ImportError:
    _HAS_NATIVE = False
else:
    _HAS_NATIVE = True


def has_native_encoder() -> bool:
    return _HAS_NATIVE


if not _HAS_NATIVE:

    def _default(value: Any) -> Any:
        module = type(value).__module__
        if module.startswith("numpy") and hasattr(value, "tolist"):
            return value.tolist()
        return str(value)

    def dumps(value: Any) -> str:
        return json.dumps(
            value,
            default=_default,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    def format_record(
        time_value: Any,
        logger: str,
        level: str,
        message: str,
        kv: Optional[Mapping[str, Any]],
    ) -> str:
        log_obj: Dict[str, Any] = {
            "time": time_value,
            "logger": logger,
            "level": level,
            "message": message,
        }

        if kv:
            log_obj.update(kv)

        return dumps(log_obj)
