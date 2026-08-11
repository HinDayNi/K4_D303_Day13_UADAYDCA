from __future__ import annotations

import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
<<<<<<< HEAD
        clear_contextvars()

        # Extract x-request-id from headers or generate a new one
        correlation_id = request.headers.get("x-request-id")
        if not correlation_id:
            correlation_id = f"req-{uuid.uuid4().hex[:8]}"
        
        # Bind the correlation_id to structlog contextvars
        bind_contextvars(correlation_id=correlation_id)
        
=======
        # Request mới bắt đầu: xóa context cũ để correlation_id/metadata không bị lẫn từ request trước.
        clear_contextvars()

        # Input: header x-request-id (nếu client đã có) hoặc không có gì.
        # Output: một correlation_id dạng req-<8 hex> dùng chung cho log / response / điều tra.
        incoming = (request.headers.get("x-request-id") or "").strip()
        if incoming:
            correlation_id = incoming
        else:
            correlation_id = f"req-{uuid.uuid4().hex[:8]}"

        # Đưa correlation_id vào structlog contextvars để mọi log trong request tự gắn cùng ID
        # (validator trừ điểm nếu service=api mà correlation_id thiếu hoặc còn "MISSING").
        bind_contextvars(correlation_id=correlation_id)

        # Lưu trên request.state để /chat trả correlation_id trong body cho client và evidence.
>>>>>>> 9ae99dc4a29048521f6dd929e79726127813abf6
        request.state.correlation_id = correlation_id

        # Đo thời gian xử lý end-to-end của request (middleware → handler → response).
        start = time.perf_counter()
        response = await call_next(request)
<<<<<<< HEAD
        
        # Add the correlation_id and processing time to response headers
        response.headers["x-request-id"] = correlation_id
        response.headers["x-response-time-ms"] = str(int((time.perf_counter() - start) * 1000))
        
=======
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        # Output ra client: cùng ID để khớp với dòng log; kèm latency để đối chiếu metrics/dashboard.
        response.headers["x-request-id"] = correlation_id
        response.headers["x-response-time-ms"] = str(elapsed_ms)

>>>>>>> 9ae99dc4a29048521f6dd929e79726127813abf6
        return response
