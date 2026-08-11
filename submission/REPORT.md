# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm:
- Repository URL:
- Commit SHA cuối:
- Thành viên và vai trò:

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 100/100 (evidence: `submission/evidence/validate_logs_result.txt`)
- Tổng số traces:
- Số PII leak còn lại: 0
- Link/đường dẫn dashboard: `data/dashboard.html`, sinh bằng `python scripts/build_dashboard.py` từ `data/logs.jsonl`

## 3. Logging và tracing

- Evidence correlation ID: `submission/evidence/log_correlation_id_sample.jsonl` (vd. `req-58374a00`)
- Evidence PII redaction: `submission/evidence/log_pii_redaction_sample.jsonl` (email/SĐT/thẻ → `[REDACTED_*]`)
- Evidence trace waterfall:
- Giải thích một span đáng chú ý:

## 4. Prompt versioning

- Prompt name:
- Version/label baseline:
- Version/label candidate:
- Trace ID của mỗi version:
- Bằng chứng đổi label hoặc rollback:

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: `HỢP LỆ: 6/6 panel có trong dashboard contract` (evidence: `submission/evidence/validate_dashboard_result.txt`)

- Evidence dashboard: `submission/evidence/dashboard_rag_slow_before.png` và `submission/evidence/dashboard_rag_slow_after.png`. Dashboard dựng bằng `scripts/build_dashboard.py`, đọc `data/logs.jsonl` và lấy ngưỡng/đơn vị/time range trực tiếp từ `config/dashboard.yaml` nên không thể lệch khỏi contract. Đủ 6 panel: Latency (p50/p95/p99), Traffic, Errors + breakdown, Cost, Tokens, Quality; mỗi panel có tên, đơn vị, cửa sổ 60 phút, refresh 30 giây và đường threshold. Kiểm tra runtime bằng `inject_incident.py --scenario rag_slow`: p95 tăng từ **1160 ms lên 3443 ms**, badge panel Latency chuyển sang "vượt ngưỡng", trong khi error rate, cost và quality giữ nguyên — chỉ một panel đổi trạng thái, đúng dấu hiệu sự cố nằm ở đường xử lý chứ không phải hệ thống hỏng toàn diện. Bảng số trong ảnh after cho thấy cả bốn phút: 09:57 (1160 ms), 09:58 (1171 ms), 10:06 (3631 ms), 10:07 (3443 ms). Chi tiết đặc tả trong `docs/dashboard-spec.md`.

- SLO đã chọn và lý do (`config/slo.yaml`): giữ nguyên `objective` để khớp threshold trong `config/dashboard.yaml`, chỉ chọn lại `target` và thêm `error_budget_minutes`. `latency_p95_ms` 3000 ms/99.0 % — dùng p95 chứ không dùng mean vì người dùng chờ theo thời gian thực; chọn 99.0 thay vì 99.5 vì retrieval và LLM là phụ thuộc bên ngoài, giữ 403 phút error budget cho deploy. `error_rate_pct` 2 %/99.5 % — target cao hơn latency vì chậm còn dùng được, lỗi thì không. `daily_cost_usd` 2.5 USD/**95.0 %**, hạ từ 100.0 vì target 100 % không để lại error budget nào, khiến mọi dao động chi phí bình thường đều thành vi phạm SLO. `quality_score_avg` 0.75/95.0 % — chỉ là proxy heuristic nên dùng theo xu hướng, không dùng để page.

- Alert rules và runbook (`config/alert_rules.yaml`, `docs/alerts.md`): 3 alert symptom-based, mỗi cái bắt một chế độ lỗi có thể inject được — `ChatResponsesTooSlow` (warning, p95 > 3000 ms, cửa sổ 10 phút, duy trì 5 phút) bắt `rag_slow`; `ChatRequestsFailing` (critical, error rate > 2 %, cửa sổ 5 phút, duy trì 2 phút) bắt `tool_fail`; `ChatCostPerRequestSpike` (warning, cost > 0.005 USD/request ≈ 2.5 lần baseline 0.001931, cửa sổ 15 phút, duy trì 10 phút) bắt `cost_spike`. Đặt tên theo triệu chứng người dùng, không theo tên implementation, vì tên hàm đổi khi code đổi còn triệu chứng thì không. Cả ba đều có `min_samples: 20` để một request lẻ ở mức tải thấp không page nhầm và để p95 không bị một request cold start kéo lệch — chính hiện tượng gặp ở CP0 khi p95 của 10 mẫu bằng luôn giá trị max 6915 ms. Ba runbook trong `docs/alerts.md` đều đi theo thứ tự Metrics → Traces → Logs, kèm lệnh cụ thể và mitigation tạm thời. `quality_score_avg` không có alert riêng vì là proxy heuristic dễ báo giả, chỉ theo dõi trên panel.

- Hạn chế đã biết: `response_sent.latency_ms` đo bên trong `app/agent.py::run` nên **không tính thời gian request xếp hàng**. Cùng một lần chạy `--concurrency 5`, log ghi 1010–1148 ms trong khi client thực sự chờ 3157–5323 ms; với `rag_slow` bật thì client chờ tới 15400 ms mà dashboard chỉ báo 3443 ms. Hệ quả là alert `ChatResponsesTooSlow` có thể không kêu dù người dùng chờ rất lâu. `app/middleware.py` đã tính sẵn `elapsed_ms` end-to-end và trả ra header `x-response-time-ms` nhưng chưa ghi vào log; ghi thêm field đó là đủ để có độ trễ thật, không phải đổi contract.

## 6. Điều tra challenge

- Challenge ID:
- Triệu chứng từ metrics:
- Trace ID liên quan:
- Log line/correlation ID liên quan:
- Root cause:
- Fix action:
- Preventive measure:

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| Thành viên 1 | Logging & PII | `scripts/collect_logging_evidence.py` + evidence Vai 1 | Structured log, correlation ID, PII redact, validate 100/100 |
| Thành viên 2 | Tracing & Prompt Versioning | | |
| Thành viên 3 | Metrics, Dashboard, SLO & Alerts | `380aea8` alert/SLO/runbook · `d3a25f6` sửa `percentile()` + `error_rate_pct` + `build_dashboard.py` · `5f96398` dashboard spec · `ce3868e` sửa layout + baseline | Percentile phải tính bằng nearest-rank và chỉ có nghĩa khi đủ mẫu: p95 của 10 request bằng luôn giá trị max, nên cold start 6915 ms bị nhầm thành baseline. Alert phải đặt theo triệu chứng người dùng kèm `for` và `min_samples`, nếu không sẽ page vì một request lẻ. Và chỉ số đo ở đâu thì chỉ nói được về chỗ đó — `latency_ms` đo trong agent nên bỏ sót thời gian xếp hàng, client chờ 15 giây mà dashboard báo 3.4 giây. |
| Thành viên 4 | Incident, Integration, Report & Demo | | |

## 8. Phân công chi tiết cho 4 thành viên

### 8.1. Thành viên 1 — Logging & PII Owner

**Mục tiêu:** bảo đảm mọi request đều truy vết được và không làm lộ dữ liệu cá nhân.

**Phạm vi phụ trách:**

- `app/logging_config.py`, `app/middleware.py`, `app/pii.py`, `app/schemas.py`.
- `config/logging_schema.json` và các test liên quan đến logging, correlation ID và PII.
- Hoàn thiện JSON structured logging.
- Tạo hoặc tiếp nhận correlation ID, truyền ID xuyên suốt request và trả lại trong response header.
- Bổ sung các metadata bắt buộc: `user_id_hash`, `session_id`, `feature`, `model`, `env`.
- Xóa context trước request mới để tránh lẫn dữ liệu giữa các request.
- Redact email, số điện thoại và số thẻ thử nghiệm trước khi render JSON và ghi log.
- Chạy load test và sửa lỗi đến khi `python scripts/validate_logs.py` đạt tối thiểu 80/100.
- Hỗ trợ Thành viên 4 tìm log theo correlation ID khi điều tra incident.

**Đầu ra và evidence:**

- Kết quả `validate_logs.py`.
- Log hợp lệ có correlation ID và đầy đủ metadata.
- Bằng chứng email, số điện thoại và số thẻ đã được che.
- Xác nhận không còn PII leak.
- Commit/PR riêng cho phần logging và PII.

### 8.2. Thành viên 2 — Tracing & Prompt Versioning Owner

**Mục tiêu:** truy vết được từng bước xử lý và xác định chính xác request đã sử dụng prompt nào.

**Phạm vi phụ trách:**

- `app/tracing.py`, `app/agent.py`, `app/prompt_management.py` và các test liên quan.
- Hoàn thiện tracing cho luồng nhận request, retrieval/RAG, chuẩn bị prompt, gọi LLM và trả response.
- Gắn correlation ID, feature, model, prompt source, `prompt_name`, `prompt_label` và `prompt_version` vào trace.
- Tạo tối thiểu 10 trace thật có metadata trên Langfuse.
- Tạo prompt `day13-chat` với ba biến `feature`, `docs` và `message`.
- Tạo version 1 có labels `baseline`, `production`; version 2 có label `candidate`.
- Chạy cùng một input với `baseline` và `candidate`, sau đó kiểm tra trace trỏ đúng version/label.
- Chuyển `production` sang version 2, chạy lại request rồi rollback về version 1.
- Không ghi giả version khi Langfuse lỗi; sử dụng đúng trạng thái `local` hoặc `local-fallback`.

**Đầu ra và evidence:**

- Danh sách tối thiểu 10 trace và một ảnh trace waterfall.
- Ảnh danh sách hai prompt version.
- Hai trace ID chứng minh `baseline` và `candidate` dùng version khác nhau.
- Bằng chứng trước/sau khi đổi label và rollback `production`.
- Commit/PR riêng cho tracing và prompt management.

### 8.3. Thành viên 3 — Metrics, Dashboard, SLO & Alerts Owner

**Mục tiêu:** tạo lớp quan sát tổng quan để phát hiện nhanh latency, lỗi, chi phí và suy giảm chất lượng.

**Phạm vi phụ trách:**

- `app/metrics.py`, `config/dashboard.yaml`, `config/slo.yaml`, `config/alert_rules.yaml` và `docs/alerts.md`.
- Dùng `data/logs.jsonl` làm nguồn dữ liệu chuẩn.
- Dựng đủ sáu nhóm panel: Latency P50/P95/P99, Traffic, Errors, Cost, Tokens và Quality.
- Mỗi panel phải có tên, đơn vị, time range và threshold hoặc SLO line rõ ràng.
- Giữ time range mặc định 60 phút và refresh 30 giây.
- Hoàn thiện SLO, alert rules và runbook dựa trên triệu chứng người dùng hoặc SLO.
- Chạy `python scripts/validate_dashboard.py` đến khi đạt 6/6 panel.
- Kiểm tra runtime bằng incident practice `rag_slow`; xác nhận P95 tăng đúng hướng rồi tắt incident.
- Hỗ trợ Thành viên 4 xác định thời gian và triệu chứng từ metrics khi điều tra challenge.

**Đầu ra và evidence:**

- Kết quả validator báo 6/6 panel hợp lệ.
- Ảnh dashboard thể hiện đủ tên panel, đơn vị, time range và threshold.
- Giá trị baseline của P95, error rate và cost.
- Bằng chứng dashboard thay đổi khi bật `rag_slow`.
- SLO, alert rules, runbook và commit/PR riêng.

### 8.4. Thành viên 4 — Incident, Integration, Report & Demo Lead

**Mục tiêu:** tích hợp kết quả của nhóm, điều tra challenge bằng evidence và bảo đảm bài nộp hợp lệ.

**Phạm vi phụ trách:**

- `app/incidents.py`, `app/challenge.py`, `scripts/inject_incident.py`, `submission/REPORT.md` và `submission/evidence/`.
- Theo dõi tiến độ, nhận evidence từ ba owner và chạy kiểm tra tích hợp sau khi merge.
- Thực hành trước với scenario `rag_slow`.
- Chỉ chạy challenge chính thức sau khi Lab Coach release `config/challenge.json`; không tự tạo hoặc sửa file này.
- Điều tra theo luồng Metrics → Trace → Span bất thường → Log cùng correlation ID → Root cause.
- Ghi rõ challenge ID, triệu chứng, khoảng thời gian, trace ID, span, correlation ID/log line, root cause, fix action và preventive measure.
- Tổng hợp report, chuẩn hóa tên file và đường dẫn trong `submission/evidence/`.
- Kiểm tra toàn bộ test, validator, Git status, secret và PII trước khi nộp.
- Tổng hợp repository URL, commit SHA và chuẩn bị kịch bản demo.

**Đầu ra và evidence:**

- Evidence điều tra challenge có metric, trace ID và log/correlation ID cụ thể.
- `submission/REPORT.md` hoàn chỉnh.
- Kết quả test và các validator cuối.
- Repository URL, commit SHA và kịch bản demo.
- Commit/PR riêng cho incident, report và tích hợp.

## 9. Kế hoạch phối hợp và bàn giao

| Thời gian | Thành viên 1 | Thành viên 2 | Thành viên 3 | Thành viên 4 |
|---|---|---|---|---|
| 0:00–0:30 | Setup, baseline log | Setup Langfuse | Kiểm tra dashboard contract | Setup repo, lập evidence checklist |
| 0:30–1:30 | Logging, correlation ID, PII | Chuẩn bị tracing | Chuẩn bị dashboard/SLO | Chạy tích hợp và hỗ trợ baseline |
| 1:30–2:30 | Bàn giao log sạch | Trace, prompt v1/v2, rollback | Hoàn thiện 6 panel và alert | Gom evidence, kiểm tra report |
| 2:30–3:30 | Hỗ trợ tìm log | Hỗ trợ tìm trace/span | Hỗ trợ xác định metric | Dẫn dắt điều tra challenge |
| 3:30–4:00 | Test và trình bày phần mình | Test và trình bày phần mình | Validator và trình bày dashboard | Report, kiểm tra Git, demo tổng |

Mỗi thành viên phải có commit/PR kiểm chứng được, tự kiểm tra evidence và giải thích được phần mình triển khai. Khi bàn giao, sử dụng mẫu sau:

```text
Hạng mục:
Commit/PR:
Lệnh kiểm tra:
Kết quả:
Evidence:
Vấn đề còn lại:
Người nhận bàn giao:
```
