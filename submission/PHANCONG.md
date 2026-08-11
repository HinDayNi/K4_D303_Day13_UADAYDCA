# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm:
- Repository URL:
- Commit SHA cuối:
- Thành viên và vai trò:

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`:
- Tổng số traces:
- Số PII leak còn lại:
- Link/đường dẫn dashboard:

## 3. Logging và tracing

- Evidence correlation ID:
- Evidence PII redaction:
- Evidence trace waterfall:
- Giải thích một span đáng chú ý:

## 4. Prompt versioning

- Prompt name:
- Version/label baseline:
- Version/label candidate:
- Trace ID của mỗi version:
- Bằng chứng đổi label hoặc rollback:

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`:
- Evidence dashboard:
- SLO đã chọn và lý do:
- Alert rules và runbook:

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
| Thành viên 1 | Logging & PII | | |
| Thành viên 2 | Tracing & Prompt Versioning | | |
| Thành viên 3 | Metrics, Dashboard, SLO & Alerts | | |
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

### 9.1. Đầu mục CP4 phải triển khai trong quá trình phối hợp

CP4 không chờ CP1–CP3 hoàn thành mới bắt đầu. CP4 chủ động triển khai và cập nhật các đầu mục sau trong suốt buổi lab:

#### Giai đoạn 0:00–0:30 — Chuẩn bị tích hợp

- [ ] Đọc `CHECKPOINTS.md`, `SUBMISSION.md`, `RUBRIC.md` và tạo checklist tiêu chí hoàn thành.
- [ ] Chạy baseline: `python -m pytest -q`, `python scripts/validate_logs.py` và `python scripts/validate_dashboard.py`.
- [ ] Ghi lại kết quả baseline, lỗi hiện có và người phụ trách xử lý từng lỗi.
- [ ] Chuẩn bị cấu trúc, quy tắc đặt tên và danh mục file trong `submission/evidence/`.
- [x] Điền trước khung `submission/REPORT.md`, repository URL, thành viên và vai trò.

#### Giai đoạn 0:30–1:30 — Theo dõi và kiểm tra tích hợp sớm

- [ ] Theo dõi tiến độ CP1, CP2, CP3; ghi rõ hạng mục đã xong, đang làm và đang bị chặn.
- [ ] Chạy smoke test `/health`, `/chat`, `/metrics` sau các lần tích hợp quan trọng.
- [ ] Kiểm tra correlation ID nối được response, log và trace; báo ngay cho CP1/CP2 nếu bị đứt chuỗi.
- [ ] Kiểm tra nhanh log/trace không chứa API key, email, số điện thoại hoặc dữ liệu nhạy cảm nguyên văn.
- [ ] Chuẩn bị kịch bản practice `rag_slow` và biểu mẫu ghi nhận Metrics → Traces → Logs.

#### Giai đoạn 1:30–2:30 — Nhận bàn giao CP1–CP3

- [ ] Nhận từ CP1: commit/PR, kết quả `validate_logs.py`, log có correlation ID và bằng chứng PII redaction.
- [ ] Nhận từ CP2: commit/PR, tối thiểu 10 trace, trace waterfall, hai trace ID cho prompt baseline/candidate và evidence rollback.
- [ ] Nhận từ CP3: commit/PR, kết quả dashboard 6/6, ảnh dashboard, baseline P95/error/cost, SLO, alert và runbook.
- [ ] Kiểm tra từng evidence có thể truy ngược về request thật; không nhận ảnh hoặc số liệu không có nguồn kiểm chứng.
- [ ] Chạy lại toàn bộ test/validator sau khi tích hợp và mở danh sách lỗi cần owner xử lý.
- [ ] Thực hành `python scripts/inject_incident.py --scenario rag_slow`, xác nhận có thể nối metric bất thường với trace và log.

#### Giai đoạn 2:30–3:30 — Điều tra challenge chính thức

- [ ] Xác nhận Lab Coach đã release `config/challenge.json`; không tự tạo, sửa hoặc thay thế file này.
- [ ] Ghi challenge ID, thời điểm bắt đầu, lệnh chạy và phạm vi dữ liệu điều tra.
- [ ] Xác định triệu chứng và khoảng thời gian bất thường từ metrics/dashboard cùng CP3.
- [ ] Chọn trace và span bất thường cùng CP2; ghi lại trace ID, tên span, latency, token và cost liên quan.
- [ ] Tìm log cùng correlation ID với CP1; lưu log line cụ thể làm bằng chứng root cause.
- [ ] Viết kết luận theo chuỗi bằng chứng: triệu chứng → trace/span → log → root cause.
- [ ] Đề xuất fix action, cách kiểm tra fix và preventive measure; không chỉ mô tả triệu chứng.

#### Giai đoạn 3:30–4:00 — Chốt bài nộp và demo

- [ ] Hoàn thiện tất cả mục trong `submission/REPORT.md`; không để placeholder bắt buộc bị trống.
- [ ] Chuẩn hóa tên và đường dẫn evidence; kiểm tra từng link/file đều mở được.
- [ ] Chạy kiểm tra cuối: `python -m pytest -q`, `python scripts/validate_logs.py`, `python scripts/validate_dashboard.py` và `git status --short`.
- [ ] Kiểm tra `.env`, API key, secret, PII, `.venv/` và cache không nằm trong Git.
- [ ] Ghi repository URL và commit SHA cuối vào báo cáo.
- [ ] Chuẩn bị demo ngắn theo luồng Metrics → Traces → Logs → Root cause → Fix → Preventive measure.
- [ ] Phân công rõ người trình bày từng màn hình và phương án dự phòng nếu Langfuse/dashboard không truy cập được lúc demo.

### 9.2. Điều kiện CP4 chấp nhận bàn giao

CP4 chỉ đánh dấu một hạng mục đã nhận khi có đủ:

1. Commit hoặc PR xác định được.
2. Lệnh kiểm tra có thể chạy lại.
3. Kết quả kiểm tra thực tế.
4. Evidence có đường dẫn rõ ràng và không chứa secret/PII.
5. Vấn đề còn lại, mức ảnh hưởng và người chịu trách nhiệm xử lý.

Nếu thiếu một trong năm mục trên, trạng thái bàn giao là **chưa hoàn tất** và phải trả lại owner tương ứng để bổ sung.

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
