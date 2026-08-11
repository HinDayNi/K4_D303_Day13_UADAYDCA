# CP4 — Hiểu công việc của từng thành viên để tích hợp

Tài liệu này giúp Thành viên 4 (Đỗ Thành Đạt) hiểu phần việc của CP1–CP3, kiểm tra bàn giao và nối các phần thành một luồng observability hoàn chỉnh.

## 1. Bức tranh tổng thể

Một request cần đi qua luồng sau:

```text
Client gửi /chat
  → CP1 tạo correlation ID, che PII và ghi JSON log
  → CP2 tạo trace/spans, gắn prompt version và metadata
  → CP3 thu thập số liệu để hiển thị metrics/dashboard
  → CP4 dùng Metrics → Traces → Logs để điều tra root cause
```

Các phần kết nối với nhau chủ yếu qua:

- `correlation_id`: nối response, log và trace của cùng một request.
- `session_id`: gom các request thuộc cùng phiên làm việc.
- `feature`: xác định chức năng bị ảnh hưởng.
- `model`: xác định model đã xử lý request.
- `prompt_name`, `prompt_label`, `prompt_version`: xác định prompt được dùng.
- Thời gian request/trace/log: khoanh vùng cùng khoảng xảy ra incident.

## 2. Thành viên 1 — Trần Thị Hương — Logging & PII

### Câu 1: Bạn thay đổi file/code nào?

Phạm vi dự kiến:

- `app/middleware.py`: nhận hoặc tạo correlation ID, bind vào context và trả ID trong response header.
- `app/main.py`: bind `user_id_hash`, `session_id`, `feature`, `model`, `env` vào log context.
- `app/logging_config.py`: cấu hình JSON structured logging và ghi `data/logs.jsonl`.
- `app/pii.py`: hash user ID, che email, số điện thoại và số thẻ.
- `config/logging_schema.json`: định nghĩa schema log bắt buộc.
- `tests/test_pii.py`, `tests/test_validate_logs.py`, `tests/test_chat_observability.py`: kiểm tra hành vi.

Trạng thái khi lập tài liệu:

- PII scrubbing và test PII đã hoạt động.
- `app/middleware.py` vẫn còn `TODO` cho correlation ID và response headers.
- `app/main.py` vẫn còn `TODO` cho log enrichment.
- `validate_logs.py` hiện đạt 60/100, chưa đạt yêu cầu 80/100.

### Câu 2: Chạy lệnh nào để chứng minh hoạt động?

```bash
python -m pytest -q tests/test_pii.py tests/test_validate_logs.py tests/test_chat_observability.py
python scripts/load_test.py
python scripts/validate_logs.py
```

Sau khi API chạy, gửi ít nhất hai request và kiểm tra:

- Mỗi response có `x-request-id` hợp lệ.
- Hai request có hai correlation ID khác nhau.
- Log `request_received` và `response_sent` của cùng request có cùng ID.
- Log có đủ `user_id_hash`, `session_id`, `feature`, `model`, `env`.
- `validate_logs.py` đạt tối thiểu 80/100.

### Câu 3: Evidence nào chứng minh kết quả?

- File kết quả `validate_logs.py` đạt từ 80/100.
- Log JSON có correlation ID và đầy đủ metadata.
- Ảnh hoặc đoạn log chứng minh email, số điện thoại và số thẻ đã được redact.
- Kết quả test CP1.
- Commit/PR riêng của CP1.

### Câu 4: Phần này kết nối với phần còn lại bằng gì?

- `correlation_id` nối log của CP1 với trace của CP2.
- `response_sent` cung cấp `latency_ms`, token, cost và quality cho dashboard CP3.
- Log giúp CP4 chứng minh root cause sau khi đã chọn được trace bất thường.

### CP4 cần hỏi Hương

1. Correlation ID được lấy từ header hay được tạo mới ở đâu?
2. ID có xuất hiện trong response, log và trace không?
3. PII được che trước hay sau khi render JSON?
4. Vì sao validator đạt/chưa đạt 80 điểm?
5. Commit, kết quả test và evidence nằm ở đâu?

## 3. Thành viên 2 — Nguyễn Thị Thanh Hiền — Tracing & Prompt Versioning

### Câu 1: Bạn thay đổi file/code nào?

Phạm vi dự kiến:

- `app/tracing.py`: khởi tạo Langfuse client và tracing adapter.
- `app/agent.py`: tạo generation trace, gắn user/session/tags và prompt metadata.
- `app/prompt_management.py`: lấy prompt theo label và fallback về prompt local.
- `tests/test_tracing_adapter.py`, `tests/test_agent_prompt_trace.py`, `tests/test_prompt_management.py`.
- Cấu hình prompt `day13-chat` trên Langfuse.

Prompt cần có:

- Version 1: labels `baseline`, `production`.
- Version 2: label `candidate`.
- Các biến `feature`, `docs`, `message`.

Trace cần thể hiện:

- `prompt_name`, `prompt_label`, `prompt_version`, `prompt_source`.
- `session_id`, user ID đã hash, feature/model dưới dạng tags hoặc metadata.
- Generation usage và cost.

### Câu 2: Chạy lệnh nào để chứng minh hoạt động?

```bash
python -m pytest -q tests/test_tracing_adapter.py tests/test_agent_prompt_trace.py tests/test_prompt_management.py
```

Kiểm tra runtime trên Langfuse:

1. Chạy cùng input với label `baseline` và `candidate`.
2. Xác nhận hai trace trỏ đến hai prompt version khác nhau.
3. Chuyển label `production` sang version 2 và chạy lại request.
4. Rollback `production` về version 1 và chạy lại.
5. Tạo tối thiểu 10 traces có metadata.

### Câu 3: Evidence nào chứng minh kết quả?

- Danh sách tối thiểu 10 traces.
- Một trace waterfall có các span/generation rõ ràng.
- Ảnh hai prompt version và labels.
- Hai trace ID cho `baseline` và `candidate`.
- Bằng chứng trước/sau đổi label và rollback `production`.
- Kết quả test và commit/PR của CP2.

### Câu 4: Phần này kết nối với phần còn lại bằng gì?

- Trace nhận `correlation_id` từ context của CP1.
- Trace metadata chứa session, feature, model và prompt version.
- CP4 dùng thời gian/correlation ID để đi từ trace bất thường về đúng log.
- Latency, token và cost trong trace có thể đối chiếu với metrics của CP3.

### CP4 cần hỏi Hiền

1. Một request tạo những trace/span nào?
2. Correlation ID được gắn vào trace ở đâu?
3. Trace nào dùng baseline, trace nào dùng candidate?
4. Có bằng chứng đổi `production` và rollback không?
5. Khi Langfuse lỗi, hệ thống ghi `local`/`local-fallback` như thế nào?

## 4. Thành viên 3 — Nguyễn Công Việt Quang — Metrics, Dashboard, SLO & Alerts

### Câu 1: Bạn thay đổi file/code nào?

Phạm vi dự kiến:

- `app/metrics.py`: ghi nhận request, latency, error, token, cost và quality.
- `config/dashboard.yaml`: định nghĩa sáu panel.
- `config/slo.yaml`: định nghĩa SLI, objective, target và error budget.
- `config/alert_rules.yaml`: định nghĩa alert rules.
- `docs/alerts.md`: runbook điều tra và xử lý alert.
- `tests/test_metrics.py`, `tests/test_dashboard_validator.py`.

Sáu nhóm panel:

1. Latency P50/P95/P99.
2. Traffic.
3. Errors.
4. Cost.
5. Tokens.
6. Quality.

Các ngưỡng hiện được cấu hình gồm latency P95 ≤ 3000 ms, error rate ≤ 2%, daily cost ≤ 2.5 USD và quality trung bình ≥ 0.75.

### Câu 2: Chạy lệnh nào để chứng minh hoạt động?

```bash
python -m pytest -q tests/test_metrics.py tests/test_dashboard_validator.py
python scripts/validate_dashboard.py
```

Kiểm tra runtime:

1. Mở `/metrics` và xác nhận dữ liệu thay đổi sau request.
2. Chạy request bình thường để ghi baseline.
3. Bật practice incident `rag_slow`.
4. Chạy thêm request và xác nhận latency/P95 tăng đúng hướng.
5. Tắt incident và xác nhận hệ thống trở lại bình thường.

### Câu 3: Evidence nào chứng minh kết quả?

- Kết quả dashboard validator đạt 6/6 panel.
- Ảnh dashboard đủ tên panel, đơn vị, time range và threshold/SLO line.
- Baseline P95, error rate, cost và quality.
- Bằng chứng dashboard thay đổi khi bật `rag_slow`.
- File SLO, alert rules và runbook.
- Kết quả test và commit/PR của CP3.

### Câu 4: Phần này kết nối với phần còn lại bằng gì?

- Metrics dùng dữ liệu từ request và `data/logs.jsonl` do CP1 tạo.
- Khi metric bất thường, CP4 dùng khoảng thời gian/feature để chọn trace của CP2.
- Token, cost và latency có thể đối chiếu giữa dashboard, trace và log.
- Alert cho biết khi nào CP4 cần bắt đầu điều tra.

### CP4 cần hỏi Quang

1. Sáu panel lấy dữ liệu từ event/trường nào?
2. P95 khác mean như thế nào và vì sao dùng P95?
3. SLO/threshold được chọn dựa trên baseline nào?
4. Alert nào page ngay, alert nào chỉ tạo ticket?
5. Khi P95 tăng, dùng dashboard để khoanh vùng thời gian ra sao?

## 5. Thành viên 4 — Đỗ Thành Đạt — Incident, Integration, Report & Demo

### Câu 1: Bạn thay đổi file/code nào?

Phạm vi dự kiến:

- `app/incidents.py`, `app/challenge.py` và `scripts/inject_incident.py`.
- `submission/REPORT.md` và `submission/evidence/`.
- Checklist tích hợp và tài liệu theo dõi bàn giao.

CP4 không làm thay CP1–CP3. CP4 nhận bàn giao, chạy lại kiểm tra, xác nhận các phần nối được với nhau và trả lỗi về đúng owner.

### Câu 2: Chạy lệnh nào để chứng minh tích hợp hoạt động?

Sau khi merge toàn bộ code:

```bash
python -m pytest -q
python scripts/validate_logs.py
python scripts/validate_dashboard.py
python scripts/inject_incident.py --scenario rag_slow
git status --short
```

CP4 còn phải smoke test:

- `/health` hoạt động.
- `/chat` trả response và correlation ID.
- `/metrics` có dữ liệu.
- Một request có thể lần theo `response → log → trace → metrics`.

### Câu 3: Evidence nào chứng minh kết quả?

- Evidence đã nhận từ CP1–CP3 và có thể chạy/kiểm tra lại.
- Evidence practice `rag_slow`.
- Evidence challenge chính thức.
- Báo cáo đã điền đầy đủ, không còn placeholder bắt buộc.
- Commit SHA cuối, kết quả test và validator cuối.
- Kịch bản demo và phân công người trình bày.

### Câu 4: Phần này kết nối với phần còn lại bằng gì?

CP4 nối toàn bộ hệ thống theo chuỗi:

```text
Dashboard cho biết triệu chứng và khoảng thời gian
  → Trace cho biết request/span nào bất thường
  → Correlation ID tìm đúng log
  → Log chứng minh root cause
  → Đề xuất fix, cách kiểm tra fix và preventive measure
```

## 6. Phân biệt triệu chứng và root cause

Ví dụ với `rag_slow`:

- **Triệu chứng:** P95 latency tăng vượt 3000 ms.
- **Khoanh vùng:** trace cho thấy span retrieval/RAG mất nhiều thời gian.
- **Bằng chứng:** log cùng correlation ID ghi request/span liên quan.
- **Root cause:** bước retrieval bị làm chậm, không phải “P95 cao”.
- **Fix action:** sửa hoặc tắt cơ chế gây chậm rồi chạy lại cùng input.
- **Preventive measure:** alert theo P95, timeout/budget cho retrieval và regression test.

`P95 cao` chỉ là triệu chứng. Root cause phải giải thích được thành phần hoặc hành vi nào tạo ra triệu chứng đó.

## 7. Tiêu chuẩn CP4 chấp nhận bàn giao

Không đánh dấu “đã nhận” nếu thiếu một trong các mục sau:

1. Commit hoặc PR xác định được.
2. Lệnh kiểm tra chạy lại được.
3. Kết quả kiểm tra thực tế.
4. Evidence có đường dẫn rõ ràng và không chứa secret/PII.
5. Vấn đề còn lại, mức ảnh hưởng và người chịu trách nhiệm.

Mẫu yêu cầu từng thành viên báo cáo:

```text
Hạng mục:
Trạng thái: Đã xong / Đang làm / Bị chặn
File đã sửa:
Commit/PR:
Lệnh kiểm tra:
Kết quả:
Evidence:
Kết nối qua ID/trường dữ liệu:
Vấn đề còn lại:
Thời gian dự kiến hoàn thành:
```

## 8. Những điều CP4 phải tự giải thích được khi demo

- Correlation ID nối response, trace và log như thế nào.
- Vì sao không được ghi PII nguyên văn vào log/trace.
- P50, P95 và P99 khác nhau như thế nào.
- Prompt version và label khác nhau như thế nào; rollback dùng để làm gì.
- SLO khác alert threshold như thế nào.
- Cách đi từ metric bất thường đến trace, log và root cause.
- Vì sao evidence phải gắn với request/trace/commit thật.
