# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- **Tên nhóm:** UADAYDCA
- **Repository:** https://github.com/HinDayNi/K4_D303_Day13_UADAYDCA
- **Mốc tổng hợp:** `origin/main` tại commit `ce3868e` (11/08/2026)

| Thành viên | Vai trò | Phạm vi chính |
|---|---|---|
| Trần Thị Hương | Logging & PII Owner | JSON logging, correlation ID, metadata, PII redaction |
| Nguyễn Thị Thanh Hiền | Tracing & Prompt Versioning Owner | Langfuse tracing, prompt metadata, dashboard và evidence |
| Nguyễn Công Việt Quang | Metrics, Dashboard, SLO & Alerts Owner | Metrics, dashboard 6 panel, SLO, alert rules và runbook |
| Đỗ Thành Đạt | Integration, Report & Demo Lead | Chuẩn hóa kế hoạch, tổng hợp đóng góp và báo cáo |

## 2. Kết quả kỹ thuật

| Hạng mục | Kết quả | Evidence |
|---|---|---|
| Logging validator | **100/100**; 19 records, 9 correlation ID, 0 PII leak khi chạy lại | `submission/evidence/validate_logs_result.txt` lưu lần bàn giao trước: 20 records, 10 correlation ID, 0 leak |
| Dashboard validator | **Hợp lệ 6/6 panel** | `config/dashboard.yaml`, `docs/dashboard-spec.md` |
| Tracing | **20 observations** gồm 10 root spans và 10 generations; dashboard hiển thị 20 traces | `submission/evidence/traces.png`, `submission/evidence/trace_waterfall.png`, `submission/evidence/dashboard.png` |
| Test tự động | Chưa chạy trọn bộ do môi trường thiếu `langfuse` và `structlog` | `python -m pytest -q` dừng ở 3 lỗi import khi collection |

## 3. Logging và tracing

- **Correlation ID:** `submission/evidence/log_correlation_id_sample.jsonl`; ví dụ `req-3bb9672f` nối `request_received` với `response_sent`.
- **PII redaction:** `submission/evidence/log_pii_redaction_sample.jsonl`; email, số điện thoại Việt Nam và số thẻ được thay bằng `[REDACTED_EMAIL]`, `[REDACTED_PHONE_VN]`, `[REDACTED_CREDIT_CARD]`.
- **Trace waterfall:** `submission/evidence/trace_waterfall.png`.
- **Span đáng chú ý:** trace `run: f80b1b263b6d6dad8f62cda31d3…` trong ảnh có tổng thời gian khoảng **1,07 s**, một generation con cùng thời gian, **206 tokens** và chi phí **0,002754 USD**. Ảnh chỉ hiển thị ID rút gọn nên không suy đoán phần còn lại.

## 4. Prompt versioning

- **Prompt name:** `day13-chat`.
- **Thiết kế:** version 1 dùng labels `baseline`, `production`; version 2 dùng label `candidate`; quy trình đổi `production` và rollback được mô tả tại `docs/PROMPT_VERSIONING.md`.
- **Triển khai trong code:** `app/prompt_management.py`, `app/agent.py`, `scripts/setup_prompt.py`; commit `4013676`, `a23dcab`.
- **Trace ID baseline/candidate và ảnh rollback:** chưa có evidence định danh trong repository tại mốc tổng hợp; cần bổ sung từ Langfuse trước khi nộp nếu rubric yêu cầu.

## 5. Dashboard, SLO và alerts

- **Validator:** `python scripts/validate_dashboard.py` trả về **HỢP LỆ: 6/6 panel**.
- **Evidence:** `submission/evidence/dashboard.png`; dashboard contract tại `config/dashboard.yaml` và đặc tả tại `docs/dashboard-spec.md`.
- **Baseline đã ghi nhận (n=10):** P50 1432 ms, P95 6915 ms, error rate 0,00%, cost 0,001965 USD/request, tokens output 124,4/request, quality 0,88. P95 bị ảnh hưởng bởi cold start và mẫu nhỏ; cần đo lại sau warm-up với n≥100.
- **SLO:** P95 ≤ 3000 ms (99,0%), error rate ≤ 2% (99,5%), daily cost ≤ 2,5 USD (95,0%), quality trung bình ≥ 0,75 (95,0%).
- **Alerts:** `high_latency_p95`, `elevated_error_rate`, `cost_budget_exceeded`; threshold và runbook nằm tại `config/alert_rules.yaml`, `docs/alerts.md`.

## 6. Điều tra challenge

- **Challenge ID:** `day13-k4-observability-v1`.
- **Incident:** `rag_slow`, feature bị ảnh hưởng `monitoring`, ngưỡng latency 2000 ms, seed 1304 (`config/challenge.json`).
- **Chuỗi điều tra dự kiến:** Metrics → trace chậm → generation/span bất thường → log cùng correlation ID → root cause.
- **Kết luận có thể chứng minh từ Git:** challenge đã được release ở commit `5ba6472`; alert latency và dashboard hỗ trợ phát hiện tail latency.
- **Evidence runtime của challenge (trace ID, correlation ID/log line, số liệu trước/sau):** chưa được commit, vì vậy chưa đủ căn cứ khẳng định root cause hoặc challenge đã được chạy thành công.
- **Fix/prevention phù hợp:** tách cold start khỏi baseline, warm-up trước khi đo, thu tối thiểu 100 request, theo dõi P95 và cảnh báo khi P95 duy trì vượt 3000 ms; với `rag_slow`, ưu tiên đo và tối ưu span retrieval/RAG sau khi có trace thực tế.

## 7. Đóng góp cá nhân

| Thành viên | Phần việc | Điều đã học |
|---|---|---|
| Trần Thị Hương | Hoàn thiện structured logging, correlation ID, PII redaction và evidence logging | Nối các log của cùng request bằng correlation ID và che dữ liệu nhạy cảm trước khi ghi log |
| Nguyễn Thị Thanh Hiền | Hoàn thiện tracing, prompt metadata và evidence dashboard, traces, trace waterfall | Gắn prompt/model metadata vào trace và sử dụng waterfall để phân tích từng bước xử lý |
| Nguyễn Công Việt Quang | Hoàn thiện metrics, dashboard, SLO, alert rules và runbook | Sử dụng percentile, SLO và cảnh báo theo triệu chứng; nhận biết sai lệch do cold start và mẫu nhỏ |
| Đỗ Thành Đạt | Tích hợp kết quả, tổng hợp evidence, hoàn thiện báo cáo và chuẩn bị demo | Tổng hợp Metrics → Traces → Logs thành chuỗi điều tra có bằng chứng rõ ràng |

## 8. Kịch bản demo

1. **Nguyễn Công Việt Quang:** mở dashboard, trình bày 6 panel, baseline, SLO và alert latency.
2. **Nguyễn Thị Thanh Hiền:** mở danh sách traces và waterfall, giải thích span/generation, tokens và cost.
3. **Trần Thị Hương:** truy log theo correlation ID và chứng minh ba loại PII đã được che.
4. **Đỗ Thành Đạt:** nối Metrics → Traces → Logs, tổng hợp root cause/fix/prevention và nêu rõ evidence còn thiếu.

## 9. Kiểm tra trước khi nộp

- [ ] Cài đủ dependency và chạy lại `python -m pytest -q` đến khi đạt.
- [x] `python scripts/validate_logs.py` đạt 100/100 và 0 PII leak.
- [x] `python scripts/validate_dashboard.py` đạt 6/6 panel.
- [x] Có evidence tối thiểu 10 traces và trace waterfall.
- [ ] Bổ sung hai trace ID cho baseline/candidate và evidence đổi label/rollback.
- [ ] Chạy challenge và bổ sung metric, trace ID, correlation ID/log line, root cause cùng kết quả fix.
- [ ] Đồng bộ local `main` với `origin/main`, cập nhật SHA cuối sau commit report và kiểm tra không có secret/PII.
