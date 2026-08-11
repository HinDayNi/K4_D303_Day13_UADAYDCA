# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

Định nghĩa máy đọc được nằm trong [`config/alert_rules.yaml`](../config/alert_rules.yaml); SLI và error budget nằm trong [`config/slo.yaml`](../config/slo.yaml). Ba bước kiểm tra của mọi runbook đều đi theo cùng một thứ tự: **Metrics xác định triệu chứng và khoảng thời gian → Traces khoanh vùng span bất thường → Logs chứng minh nguyên nhân**. Không kết luận khi mới có một lớp evidence.

Baseline tham chiếu (đo 2026-08-11, n=10 request, chưa bật incident): latency p50 1432 ms, cost 0.001965 USD/request, tokens_out 124.4/request, quality 0.88, error rate 0.00 %.

## Alert 1

- Tên: `ChatResponsesTooSlow`
- Severity: warning — tạo ticket, không page lúc nửa đêm; người dùng vẫn nhận được câu trả lời.
- SLI/SLO liên quan: `latency_p95_ms`, objective 3000 ms, target 99.0 % trong 28 ngày (error budget 403 phút).
- Điều kiện và thời gian duy trì: `p95(response_sent.latency_ms)` trên cửa sổ 10 phút vượt 3000 ms và **duy trì 5 phút liên tục**, với tối thiểu 20 request trong cửa sổ. Ràng buộc 20 request để p95 không bị một request cold start kéo lệch — đúng hiện tượng đã thấy ở baseline, nơi p95 của 10 mẫu bằng luôn giá trị max 6915 ms.
- Ảnh hưởng tới người dùng: người dùng chờ hơn 3 giây mới thấy câu trả lời, giao diện chat có cảm giác treo và tỷ lệ bỏ ngang tăng.
- Ba bước kiểm tra đầu tiên:
  1. **Metrics** — mở panel `latency`, ghi lại thời điểm p95 bắt đầu vượt ngưỡng. Đối chiếu ngay panel `traffic`: nếu request/phút phẳng mà latency tăng thì đây **không** phải quá tải, mà là một bước trong pipeline chậm đi. So p50 với p95: p50 cũng tăng nghĩa là mọi request đều chậm; chỉ p95 tăng nghĩa là vấn đề ở phần đuôi.
  2. **Traces** — mở Langfuse, lọc trace trong khoảng thời gian đó, sắp xếp theo duration giảm dần rồi mở waterfall của trace chậm nhất. So thời lượng span retrieval với span generation: `app/agent.py::run` gọi `retrieve()` trước rồi mới gọi LLM, nên waterfall chỉ rõ được bước nào chiếm phần lớn thời gian.
  3. **Logs** — lấy `correlation_id` của trace đó và tìm trong log, so `latency_ms` với baseline p50 1432 ms:
     ```powershell
     Select-String -Path data/logs.jsonl -Pattern "<correlation_id>"
     ```
     Kiểm tra thêm `GET /health` xem trường `incidents` có scenario nào đang bật không.
- Mitigation tạm thời: nếu `/health` cho thấy incident đang bật, tắt bằng `python scripts/inject_incident.py --scenario rag_slow --disable`. Nếu là chậm thật ở retrieval, cho `retrieve()` chạy với timeout ngắn và rơi về câu trả lời không dùng RAG thay vì chờ vô hạn — chấp nhận giảm chất lượng để giữ độ trễ. Giảm concurrency của client nếu độ trễ đến từ tranh chấp tài nguyên.
- Owner: Thành viên 3 (Metrics, Dashboard, SLO & Alerts); chuyển tiếp Thành viên 2 khi cần đọc sâu trace.

## Alert 2

- Tên: `ChatRequestsFailing`
- Severity: critical — page ngay, kể cả ngoài giờ.
- SLI/SLO liên quan: `error_rate_pct`, objective 2 %, target 99.5 % trong 28 ngày (error budget 201 phút).
- Điều kiện và thời gian duy trì: `count(request_failed) / count(request_received)` trên cửa sổ 5 phút vượt 2 % và **duy trì 2 phút liên tục**, với tối thiểu 20 request trong cửa sổ. Cửa sổ và thời gian duy trì ngắn hơn alert 1 vì lỗi không có đường vòng nào cho người dùng. Ràng buộc 20 request là bắt buộc: ở mức tải 10 request, một lỗi lẻ đã thành 10 % và sẽ page nhầm.
- Ảnh hưởng tới người dùng: người dùng nhận HTTP 500 và không có câu trả lời nào; không tự xử lý được, buộc phải thử lại hoặc rời đi.
- Ba bước kiểm tra đầu tiên:
  1. **Metrics** — mở panel `errors`, đọc error rate và breakdown theo `error_type`. Nếu lỗi dồn vào **một** `error_type` thì đây là lỗi có hệ thống chứ không phải nhiễu; ghi lại tên loại lỗi đó, nó là từ khóa cho hai bước sau. Đối chiếu panel `traffic` để biết lỗi xảy ra trên toàn bộ hay chỉ một phần lưu lượng.
  2. **Traces** — mở một trace của request lỗi trong khoảng đó và tìm span không hoàn tất. Span dừng ở đâu thì lỗi phát sinh ở đó; ghi lại `correlation_id` của trace.
  3. **Logs** — đọc log lỗi để lấy thông điệp gốc, đây là bằng chứng root cause:
     ```powershell
     Select-String -Path data/logs.jsonl -Pattern '"event": "request_failed"' | Select-Object -Last 5
     ```
     Trường `error_type` và `payload.detail` cho thông điệp nguyên văn (ví dụ `RuntimeError` kèm `Vector store timeout` phát ra từ [`app/mock_rag.py`](../app/mock_rag.py)). Đối chiếu `correlation_id` ở bước 2 để chắc chắn đang đọc đúng request.
- Mitigation tạm thời: kiểm tra `GET /health` trường `incidents` trước tiên; nếu do incident injection thì tắt scenario tương ứng. Nếu là lỗi thật ở retrieval, chuyển `retrieve()` sang chế độ suy giảm có kiểm soát — bắt exception và trả về fallback document thay vì để exception nổi lên thành 500. Người dùng nhận câu trả lời chất lượng thấp hơn còn hơn không nhận gì; đồng thời error rate trở về trong SLO trong lúc sửa gốc.
- Owner: Thành viên 4 (Incident, Integration, Report & Demo); phối hợp Thành viên 1 để tra log theo correlation ID.

## Alert 3

- Tên: `ChatCostPerRequestSpike`
- Severity: warning — tạo ticket trong giờ làm việc.
- SLI/SLO liên quan: `daily_cost_usd`, objective 2.5 USD/ngày, target 95.0 % trong 28 ngày.
- Điều kiện và thời gian duy trì: `mean(response_sent.cost_usd)` trên cửa sổ 15 phút vượt 0.005 USD/request và **duy trì 10 phút liên tục**, với tối thiểu 20 request. Ngưỡng 0.005 tương đương khoảng 2.5 lần baseline 0.001965 USD/request. Cửa sổ dài nhất trong ba alert vì chi phí không phải sự cố cần phản ứng tức thì, và độ dài câu trả lời vốn dao động tự nhiên.
- Ảnh hưởng tới người dùng: chưa ảnh hưởng trực tiếp — người dùng vẫn nhận câu trả lời đúng hạn. Nhưng nếu để nguyên, ngân sách 2.5 USD/ngày cạn sớm và dẫn tới rate limit hoặc cắt dịch vụ, lúc đó ảnh hưởng mới xuất hiện và nặng hơn nhiều.
- Ba bước kiểm tra đầu tiên:
  1. **Metrics** — mở đồng thời panel `cost` và panel `tokens`, và tách hai khả năng: chi phí tăng do **nhiều request hơn** (panel `traffic` tăng theo — đây là tăng trưởng bình thường, không phải sự cố) hay do **mỗi request đắt hơn** (traffic phẳng nhưng `tokens_out` trên mỗi request tăng — đây mới là sự cố). So `tokens_out` với baseline 124.4/request. Đọc luôn tổng chi phí trong cửa sổ 60 phút trên panel `cost` để ước lượng còn bao lâu thì chạm trần 2.5 USD.
  2. **Traces** — mở một trace đắt tiền và đọc `usage_details.completion_tokens` cùng metadata `prompt_name`, `prompt_label`, `prompt_version`. Nếu chi phí bắt đầu tăng đúng lúc `prompt_version` đổi thì thay đổi prompt chính là nghi phạm hàng đầu.
  3. **Logs** — xác nhận bằng số liệu thô, chi phí phải khớp công thức `tokens_out x 15 / 1e6 + tokens_in x 3 / 1e6` trong [`app/agent.py`](../app/agent.py)`::_estimate_cost`:
     ```powershell
     Select-String -Path data/logs.jsonl -Pattern '"event": "response_sent"' | Select-Object -Last 20
     ```
     Nếu `tokens_out` tăng còn `tokens_in` giữ nguyên thì nguyên nhân nằm ở phía sinh output, không phải ở prompt đầu vào.
- Mitigation tạm thời: nếu nguyên nhân là prompt version mới, rollback label `production` về version trước theo [PROMPT_VERSIONING.md](PROMPT_VERSIONING.md) — đây là cách khôi phục nhanh nhất và không cần deploy. Nếu không phải, đặt giới hạn `max_tokens` cho lời gọi LLM để chặn trần chi phí mỗi request. Nếu do incident injection thì tắt bằng `python scripts/inject_incident.py --scenario cost_spike --disable`.
- Owner: Thành viên 3 (Metrics, Dashboard, SLO & Alerts); chuyển tiếp Thành viên 2 khi nghi ngờ do prompt version.

## Ghi chú về cửa sổ đánh giá khi demo

Các giá trị `window` và `for` ở trên được đặt theo tiêu chuẩn vận hành thật, nơi lưu lượng liên tục. Trong buổi lab, một lần `python scripts/load_test.py` chỉ chạy vài chục giây nên không alert nào kịp duy trì đủ thời gian để bắn.

Khi demo, hãy trình bày điều kiện thật ở trên rồi chứng minh **triệu chứng vượt ngưỡng** trên dashboard trước/sau khi bật incident, thay vì hạ `for` xuống 0 để alert kêu cho đẹp. Hạ thời gian duy trì để lấy ảnh chính là dạng lỗi mà `min_samples` và `for` sinh ra để phòng, và người chấm sẽ hỏi đúng chỗ đó.
