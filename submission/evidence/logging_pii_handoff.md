# Bàn giao Vai 1 — Logging & PII

- Thời điểm (UTC): 2026-08-11T08:40:44.696996+00:00
- Điểm `validate_logs.py`: 100/100
- Ngưỡng lab: ≥ 80/100

## Evidence (đường dẫn tương đối)

- Kết quả validator: `submission/evidence/validate_logs_result.txt`
- Mẫu correlation ID + metadata: `submission/evidence/log_correlation_id_sample.jsonl` (6 dòng)
- Mẫu PII đã redact: `submission/evidence/log_pii_redaction_sample.jsonl` (3 dòng)
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
Kết quả: 100/100
Evidence: submission/evidence/validate_logs_result.txt
Vấn đề còn lại: chụp ảnh màn hình validator nếu Lab Coach yêu cầu screenshot
Người nhận bàn giao: Thành viên 4
```
