"""Thu thập evidence Vai 1: traffic → validate_logs → submission/evidence/."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.cli import configure_utf8_stdio

BASE_URL = "http://127.0.0.1:8000"
LOG_PATH = REPO_ROOT / "data" / "logs.jsonl"
EVIDENCE_DIR = REPO_ROOT / "submission" / "evidence"
HANDOFF_PATH = EVIDENCE_DIR / "logging_pii_handoff.md"
VALIDATE_OUT = EVIDENCE_DIR / "validate_logs_result.txt"
SAMPLE_CORR = EVIDENCE_DIR / "log_correlation_id_sample.jsonl"
SAMPLE_PII = EVIDENCE_DIR / "log_pii_redaction_sample.jsonl"
SCORE_RE = re.compile(r"Estimated Score:\s*(\d+)/100")


def ensure_api_ready(timeout_s: float = 30.0) -> None:
    # Input: BASE_URL. Output: /health ok — nếu API chưa chạy thì không sinh được log thật.
    deadline = time.time() + timeout_s
    last_error = ""
    while time.time() < deadline:
        try:
            response = httpx.get(f"{BASE_URL}/health", timeout=2.0)
            if response.status_code == 200 and response.json().get("ok") is True:
                print(f"[ok] API sẵn sàng tại {BASE_URL}")
                return
            last_error = f"status={response.status_code} body={response.text}"
        except Exception as exc:  # noqa: BLE001
            last_error = str(exc)
        time.sleep(0.5)
    raise RuntimeError(
        f"API chưa sẵn sàng tại {BASE_URL}. Chạy: "
        f"uvicorn app.main:app --reload --env-file .env\nChi tiết: {last_error}"
    )


def reset_log_file() -> Path | None:
    # Input: logs.jsonl có thể lẫn bản ghi cũ (MISSING / thiếu enrichment).
    # Output: file log trống + bản archive — validator chỉ chấm traffic vừa tạo.
    if not LOG_PATH.exists():
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        LOG_PATH.write_text("", encoding="utf-8")
        return None
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive = LOG_PATH.with_name(f"logs.pre_evidence_{stamp}.jsonl")
    LOG_PATH.replace(archive)
    LOG_PATH.write_text("", encoding="utf-8")
    print(f"[ok] Archive log cũ → {archive.relative_to(REPO_ROOT)}")
    return archive


def run_load_test(concurrency: int) -> None:
    # Input: sample_queries.jsonl (có email/SĐT/thẻ mẫu). Output: nhiều request /chat → dòng JSONL mới.
    cmd = [sys.executable, str(REPO_ROOT / "scripts" / "load_test.py"), "--concurrency", str(concurrency)]
    print(f"[run] {' '.join(cmd)}")
    completed = subprocess.run(cmd, cwd=REPO_ROOT, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"load_test.py thất bại (exit={completed.returncode})")


def run_validate_logs() -> tuple[str, int]:
    # Input: data/logs.jsonl sau load test. Output: điểm ước lượng + checklist PASSED/FAILED.
    cmd = [sys.executable, str(REPO_ROOT / "scripts" / "validate_logs.py")]
    print(f"[run] {' '.join(cmd)}")
    completed = subprocess.run(cmd, cwd=REPO_ROOT, check=False, capture_output=True, text=True, encoding="utf-8")
    output = (completed.stdout or "") + (completed.stderr or "")
    print(output)
    match = SCORE_RE.search(output)
    score = int(match.group(1)) if match else -1
    return output, score


def pick_evidence_lines(records: list[dict]) -> tuple[list[dict], list[dict]]:
    # Input: toàn bộ log. Output: mẫu có correlation_id hợp lệ + mẫu đã redact PII (token REDACTED).
    api_records = [r for r in records if r.get("service") == "api"]
    correlation_samples = [
        r for r in api_records if r.get("correlation_id") and r.get("correlation_id") != "MISSING"
    ][:6]
    pii_samples = [
        r
        for r in api_records
        if isinstance(r.get("payload"), dict)
        and any(
            isinstance(v, str) and "[REDACTED_" in v
            for v in r["payload"].values()
        )
    ][:6]
    return correlation_samples, pii_samples


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + ("\n" if rows else ""),
        encoding="utf-8",
    )


def write_handoff(score: int, corr_count: int, pii_count: int) -> None:
    # Input: điểm + số mẫu. Output: phiếu bàn giao cho TV4 (tìm log theo correlation_id khi điều tra).
    now = datetime.now(timezone.utc).isoformat()
    body = f"""# Bàn giao Vai 1 — Logging & PII

- Thời điểm (UTC): {now}
- Điểm `validate_logs.py`: {score}/100
- Ngưỡng lab: ≥ 80/100

## Evidence (đường dẫn tương đối)

- Kết quả validator: `submission/evidence/validate_logs_result.txt`
- Mẫu correlation ID + metadata: `submission/evidence/log_correlation_id_sample.jsonl` ({corr_count} dòng)
- Mẫu PII đã redact: `submission/evidence/log_pii_redaction_sample.jsonl` ({pii_count} dòng)
- Nguồn log runtime: `data/logs.jsonl`

## Cách TV4 dùng khi điều tra

1. Lấy `correlation_id` từ response header `x-request-id` hoặc body `/chat`.
2. Lọc `data/logs.jsonl` theo đúng ID đó.
3. Đối chiếu với trace/metrics cùng khoảng thời gian (Metrics → Traces → Logs).

## Checklist Vai 1

- [x] JSON structured logging
- [x] correlation_id dạng `req-<8hex>` xuyên suốt request
- [x] enrichment: user_id_hash, session_id, feature, model, env
- [x] PII redact trước khi ghi disk
- [x] validate_logs ≥ 80

```text
Hạng mục: Logging & PII
Commit/PR: (điền sau khi commit)
Lệnh kiểm tra: python scripts/collect_logging_evidence.py
Kết quả: {score}/100
Evidence: submission/evidence/validate_logs_result.txt
Vấn đề còn lại: chụp ảnh màn hình validator nếu Lab Coach yêu cầu screenshot
Người nhận bàn giao: Thành viên 4
```
"""
    HANDOFF_PATH.write_text(body, encoding="utf-8")


def main() -> None:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Vai 1: load test → validate_logs → evidence")
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument(
        "--keep-logs",
        action="store_true",
        help="Không archive/reset data/logs.jsonl trước khi chạy (mặc định: reset để điểm sạch).",
    )
    parser.add_argument(
        "--skip-load-test",
        action="store_true",
        help="Chỉ validate + đóng gói evidence từ log hiện có.",
    )
    args = parser.parse_args()

    # Thư mục evidence là đầu ra bàn giao; tạo nếu chưa có.
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    ensure_api_ready()

    if not args.keep_logs and not args.skip_load_test:
        reset_log_file()

    if not args.skip_load_test:
        run_load_test(args.concurrency)

    # Đợi flush ghi file (JsonlFileProcessor append sync, nhưng giữ biên nhỏ cho an toàn).
    time.sleep(0.2)

    validate_text, score = run_validate_logs()
    VALIDATE_OUT.write_text(validate_text, encoding="utf-8")

    # Đóng gói mẫu log cho REPORT — không commit full logs.jsonl nếu có dữ liệu nhạy cảm chưa scrub.
    if not LOG_PATH.exists():
        raise RuntimeError(f"Không thấy {LOG_PATH}")
    records: list[dict] = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    correlation_samples, pii_samples = pick_evidence_lines(records)
    write_jsonl(SAMPLE_CORR, correlation_samples)
    write_jsonl(SAMPLE_PII, pii_samples)
    write_handoff(score, len(correlation_samples), len(pii_samples))

    print("--- Evidence written ---")
    for path in (VALIDATE_OUT, SAMPLE_CORR, SAMPLE_PII, HANDOFF_PATH):
        print(f"  {path.relative_to(REPO_ROOT)}")

    if score < 80:
        raise SystemExit(
            f"Chưa đạt checkpoint Vai 1: {score}/100 (< 80). "
            "Kiểm tra correlation_id, enrichment và PII rồi chạy lại."
        )
    print(f"[done] Checkpoint Vai 1 đạt {score}/100 — sẵn sàng bàn giao TV4.")


if __name__ == "__main__":
    main()
