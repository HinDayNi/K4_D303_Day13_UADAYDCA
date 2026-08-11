# Yêu cầu dashboard

Contract có thể kiểm tra bằng máy nằm tại `config/dashboard.yaml`. Hướng dẫn dựng và kiểm tra runtime nằm tại [DASHBOARD_SETUP.md](DASHBOARD_SETUP.md).

Dashboard chính cần đủ 6 nhóm thông tin:

1. Latency P50/P95/P99.
2. Traffic: request count hoặc QPS.
3. Error rate và breakdown theo loại lỗi.
4. Cost theo thời gian.
5. Tổng token input/output.
6. Quality proxy.

Tiêu chuẩn trình bày:

- Khoảng thời gian mặc định: 1 giờ.
- Tự refresh mỗi 15–30 giây nếu công cụ hỗ trợ.
- Có threshold hoặc SLO line.
- Ghi rõ đơn vị.
- Chỉ giữ 6–8 panel quan trọng ở lớp chính.
- Screenshot phải nhìn được tên panel và khoảng thời gian.

Kiểm tra contract trước khi chụp evidence:

```bash
python scripts/validate_dashboard.py
```

## Công cụ nhóm sử dụng

`scripts/build_dashboard.py` — sinh một file HTML tự chứa từ `data/logs.jsonl`.

```bash
python scripts/build_dashboard.py --open
```

Chọn cách này thay vì Grafana hoặc Streamlit vì không phải thêm dependency mới vào `requirements.txt` giữa buổi lab — script chỉ dùng `PyYAML` đã có sẵn, nên mọi thành viên chạy được ngay mà không cần cài thêm gì.

Script đọc `time_range_minutes`, `refresh_seconds`, đơn vị và threshold **trực tiếp từ `config/dashboard.yaml`**, nên dashboard không thể lệch khỏi contract mà `validate_dashboard.py` kiểm tra. Đổi ngưỡng trong YAML thì dashboard đổi theo, không phải sửa code.

Tuỳ chọn khác:

| Cờ | Tác dụng |
|---|---|
| `--out <path>` | đổi file đầu ra, dùng để giữ ảnh before/after khi test incident |
| `--minutes N` | ghi đè time range |
| `--logs <path>` | đọc file log khác |

## Đặc tả sáu panel

Cửa sổ mặc định 60 phút, tự refresh 30 giây, mọi panel có threshold vẽ thành đường đứt nét kèm nhãn.

| # | Panel | Event/field | Phép tổng hợp | Đơn vị | Threshold | Dạng biểu đồ |
|---|---|---|---|---|---|---|
| 1 | Latency percentiles | `response_sent.latency_ms` | p50, p95, p99 theo từng phút | ms | p95 ≤ 3000 | 3 đường, cùng một màu đậm dần |
| 2 | Request traffic | `request_received` | count theo phút | requests_per_minute | ≥ 1 | cột |
| 3 | Error rate and breakdown | `request_received`, `request_failed`, `error_type` | error_rate_pct + count theo `error_type` | percent | ≤ 2 | cột + bảng breakdown |
| 4 | Cost over time | `response_sent.cost_usd` | tổng theo phút, tổng cửa sổ | usd | tổng ≤ 2.5 | cột |
| 5 | Input and output tokens | `response_sent.tokens_in/tokens_out` | tổng theo phút, tổng theo từng field | tokens | ≤ 50000 | cột chồng |
| 6 | Quality proxy | `response_sent.quality_score` | trung bình theo phút | score_0_to_1 | ≥ 0.75 | đường |

Ghi chú trình bày:

- Panel 1 dùng **một màu xanh đậm dần** cho p50 → p95 → p99 thay vì ba màu khác nhau, vì đây là ba mức của cùng một đại lượng chứ không phải ba đối tượng khác nhau.
- Panel 3 dùng màu status đỏ, không dùng màu định danh, vì request lỗi mang nghĩa xấu. Các cột trong breakdown dùng chung một màu vì `error_type` là danh mục không có thứ tự.
- Bảng màu đã chạy qua validator colorblind-safe ở cả light mode và dark mode.
- Mọi giá trị trên biểu đồ đều có trong bảng "Xem dạng bảng" ở cuối trang, nên không giá trị nào chỉ đọc được qua tooltip.

## Baseline

Đo lúc 2026-08-11 09:57–09:58 UTC, 20 request, chưa bật incident, sau khi warm-up:

| Chỉ số | Giá trị |
|---|---|
| Latency p50 / p95 / p99 | 1062 / 1160 / 1171 ms |
| Traffic | 10 request/phút |
| Error rate | 0.00 % |
| Cost | 0.038625 USD tổng · 0.001931 USD/request |
| Tokens in / out | 660 / 2443 (122.2 out/request) |
| Quality trung bình | 0.880 |

Baseline này thay thế số đo ở CP0 (p95 6915 ms). Giá trị cũ là cold start của request đầu tiên khi khởi tạo Langfuse client; với n = 10 thì p95 gần như bằng max nên một request chậm đã kéo lệch cả chỉ số. Luôn chạy `load_test.py` một lượt để warm-up rồi bỏ kết quả trước khi đo.

Phân bố latency chia thành hai cụm rõ rệt: 414–435 ms (7 request) và 1050–1171 ms (13 request). Cụm chậm là những request phải gọi Langfuse để lấy prompt `day13-chat`; cụm nhanh là những request rơi vào lúc SDK đã cache kết quả nên không đi mạng. Đây là lý do p50 không đại diện cho hệ thống này và tại sao mọi ngưỡng đều đặt trên p95.

## Hạn chế đã biết: `latency_ms` không phải độ trễ người dùng cảm nhận

`response_sent.latency_ms` đo trong `app/agent.py::run`, tính từ lúc agent bắt đầu chạy đến lúc xong. Nó **không bao gồm thời gian request nằm chờ trong hàng đợi**.

Bằng chứng, cùng một lần chạy `load_test.py --concurrency 5`:

| Nguồn đo | Giá trị |
|---|---|
| `latency_ms` trong log (20 request) | 1010 – 1148 ms |
| Thời gian client thực sự chờ | 3157 – 5323 ms |

Chênh lệch đến từ việc `agent.run` là code đồng bộ chạy trong endpoint `async`, nên nó chặn event loop và các request đồng thời bị xếp hàng. Người dùng chờ 5.3 giây trong khi dashboard báo 1.1 giây.

Hệ quả cần biết khi đọc dashboard và khi trực alert:

- Panel Latency và SLO `latency_p95_ms` đang đo thời gian xử lý của agent, không phải thời gian người dùng chờ.
- Alert `ChatResponsesTooSlow` sẽ **không** kêu trong tình huống trên, dù triệu chứng người dùng là rất rõ.

Cách khắc phục: `app/middleware.py` đã tính sẵn `elapsed_ms` end-to-end và trả ra header `x-response-time-ms`, nhưng giá trị này chưa được ghi vào log nên dashboard không thấy được. Ghi thêm nó thành một field của `response_sent` là đủ để có độ trễ end-to-end thật, không phải đổi contract — panel Latency vẫn giữ `latency_ms`, chỉ thêm một đường nữa để so sánh.
