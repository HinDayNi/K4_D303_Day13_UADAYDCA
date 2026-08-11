# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

Định nghĩa máy đọc được nằm trong [`config/alert_rules.yaml`](../config/alert_rules.yaml); SLI và error budget nằm trong [`config/slo.yaml`](../config/slo.yaml). Ba bước kiểm tra của mọi runbook đều đi theo cùng một thứ tự: **Metrics xác định triệu chứng và khoảng thời gian → Traces khoanh vùng span bất thường → Logs chứng minh nguyên nhân**. Không kết luận khi mới có một lớp evidence.

Baseline tham chiếu (đo 2026-08-11, n=10 request, chưa bật incident): latency p50 1432 ms, cost 0.001965 USD/request, tokens_out 124.4/request, quality 0.88, error rate 0.00 %.

## Alert 1

- Tên: `high_latency_p95`
- Severity: `warning`
- SLI/SLO liên quan: `latency_p95_ms` (Mục tiêu P95 dưới 3000ms)
- Điều kiện và thời gian duy trì: P95 Latency > 3000ms duy trì liên tục trong 5 phút.
- Ảnh hưởng tới người dùng: Chatbot phản hồi rất chậm, khiến người dùng phải chờ đợi lâu, gây ức chế và trải nghiệm tồi tệ.
- Ba bước kiểm tra đầu tiên:
  1. Kiểm tra biểu đồ phân rã (breakdown) thời gian trên Langfuse để xem độ trễ đến từ phần truy xuất tài liệu (RAG/VectorDB) hay từ quá trình sinh text của LLM.
  2. Kiểm tra trang status của nhà cung cấp LLM (như OpenAI, Anthropic) xem API của họ có đang bị nghẽn hay suy giảm hiệu năng không.
  3. Kiểm tra tài nguyên máy chủ (CPU, Memory) hoặc logs để xem có hiện tượng nghẽn cổ chai (bottleneck) cục bộ hay timeout loop nào không.
- Mitigation tạm thời: Chuyển đổi (fallback) sang model LLM nhỏ hơn/nhanh hơn. Nếu RAG bị chậm, có thể tạm thời vô hiệu hóa tính năng tìm kiếm tài liệu phức tạp để ưu tiên tốc độ phản hồi cơ bản.
- Owner: `on-call-engineer`

## Alert 2

- Tên: `elevated_error_rate`
- Severity: `critical`
- SLI/SLO liên quan: `error_rate_pct` (Mục tiêu Error Rate dưới 2%)
- Điều kiện và thời gian duy trì: Tỷ lệ lỗi (error rate) > 5% duy trì liên tục trong 3 phút.
- Ảnh hưởng tới người dùng: Người dùng nhận thông báo lỗi liên tục, không nhận được câu trả lời. Hệ thống dường như đang bị sập từ góc nhìn của họ.
- Ba bước kiểm tra đầu tiên:
  1. Nhìn vào bảng Error Breakdown trên Dashboard để xác định nhanh loại lỗi phổ biến (Ví dụ: HTTP 500, 429 Too Many Requests, hay 401 Unauthorized).
  2. Lọc (filter) các trace bị lỗi trên Langfuse, xem chi tiết Stacktrace để xác định xem lỗi văng ra ở bước nào (Kết nối DB lỗi, LLM API key hết hạn, hay lỗi logic code).
  3. Kiểm tra lịch sử hệ thống xem có đợt triển khai (deployment) hoặc thay đổi cấu hình nào vừa mới diễn ra trong vài phút trước đó không.
- Mitigation tạm thời: Nếu lỗi do đợt triển khai mới, lập tức Rollback về phiên bản cũ ổn định. Nếu do API bên thứ 3 quá tải/rate-limit, kích hoạt cơ chế fallback (chuyển sang provider khác hoặc trả về câu trả lời cache).
- Owner: `on-call-engineer`

## Alert 3

- Tên: `cost_budget_exceeded`
- Severity: `warning`
- SLI/SLO liên quan: `daily_cost_usd` (Mục tiêu chi phí dưới 2.5 USD/ngày)
- Điều kiện và thời gian duy trì: Chi phí trong ngày tích lũy vượt mức 2.5 USD.
- Ảnh hưởng tới người dùng: Không có ảnh hưởng trực tiếp ngay lập tức, nhưng nếu tài khoản cạn tiền, API sẽ bị chặn và toàn hệ thống sẽ ngừng hoạt động.
- Ba bước kiểm tra đầu tiên:
  1. Kiểm tra Dashboard để xem lưu lượng (Traffic/QPS) có tăng vọt bất thường (nghi ngờ bị tấn công DDoS hoặc bot spam) hay không.
  2. Vào Langfuse lọc các trace tiêu thụ nhiều Token nhất, kiểm tra xem có prompt nào dài bất thường hoặc đang bị lặp vô hạn không.
  3. Kiểm tra xem gần đây có sự thay đổi config nào chuyển hệ thống sang sử dụng model đắt tiền hơn dự kiến hay không.
- Mitigation tạm thời: Thiết lập giới hạn Rate Limit nghiêm ngặt hơn hoặc block các IP/User ID đang có dấu hiệu spam. Chuyển cấu hình LLM sang model rẻ hơn cho đến khi nguyên nhân được giải quyết triệt để.
- Owner: `team-lead`
