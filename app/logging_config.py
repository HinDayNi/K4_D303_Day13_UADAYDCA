from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import structlog
from structlog.contextvars import merge_contextvars

from .pii import scrub_text

LOG_PATH = Path(os.getenv("LOG_PATH", "data/logs.jsonl"))


class JsonlFileProcessor:
    def __call__(self, logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
        # Input: event_dict đã qua scrub → Output: một dòng JSON bổ sung vào data/logs.jsonl trên disk.
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        rendered = structlog.processors.JSONRenderer()(logger, method_name, event_dict)
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(rendered + "\n")
        return event_dict


def scrub_event(_: Any, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    # Input: event_dict còn có thể chứa PII trong payload/event.
    # Chỉ scrub giá trị chuỗi trong payload — giữ số liệu latency/token/cost nguyên để dashboard dùng.
    payload = event_dict.get("payload")
    if isinstance(payload, dict):
        event_dict["payload"] = {
            k: scrub_text(v) if isinstance(v, str) else v for k, v in payload.items()
        }

    # Tên event cũng có thể dính PII nếu ai đó nhét text người dùng vào field này.
    if "event" in event_dict and isinstance(event_dict["event"], str):
        event_dict["event"] = scrub_text(event_dict["event"])

    # Output: cùng event_dict nhưng đã an toàn để render JSON và ghi xuống disk.
    return event_dict


def configure_logging() -> None:
    # Thiết lập mức log từ môi trường; mọi request sau đó đi chung một pipeline processor.
    logging.basicConfig(format="%(message)s", level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")))

    # Thứ tự processor = luồng dữ liệu bắt buộc:
    # contextvars → level/ts → scrub PII → (stack/exc) → ghi file → render console.
    # scrub_event phải đứng TRƯỚC JsonlFileProcessor; nếu không, load test vẫn leak PII trên disk.
    structlog.configure(
        processors=[
            merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True, key="ts"),
            scrub_event,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            JsonlFileProcessor(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )


def get_logger() -> structlog.typing.FilteringBoundLogger:
    # Output: logger đã gắn pipeline trên; caller chỉ cần truyền event + field nghiệp vụ.
    return structlog.get_logger()
