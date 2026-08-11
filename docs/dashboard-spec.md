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

## Chi tiết Dashboard Spec

Dưới đây là đặc tả chi tiết 6 nhóm chỉ số trên dashboard, dựa theo cấu hình thực tế trong file `config/dashboard.yaml`:

| # | Nhóm Panel | Tên Panel | Đơn vị | Khoảng thời gian | Threshold / SLO line | Nguồn dữ liệu |
|---|---|---|---|---|---|---|
| 1 | **Latency** | Latency percentiles | `ms` | 60 phút (refresh 30s) | p95 <= 3000 ms | `/metrics` → `latency_p50`, `latency_p95`, `latency_p99` |
| 2 | **Traffic** | Request traffic | `requests_per_minute` | 60 phút (refresh 30s) | rate_per_minute >= 1 | `/metrics` → `traffic` |
| 3 | **Error** | Error rate and breakdown | `%` (percent) | 60 phút (refresh 30s) | error_rate_pct <= 2% | `/metrics` → `error_rate_pct`, `error_breakdown` |
| 4 | **Cost** | Cost over time | `usd` | 60 phút (refresh 30s) | total <= 2.5 USD | `/metrics` → `total_cost_usd`, `avg_cost_usd` |
| 5 | **Tokens** | Input and output tokens | `tokens` | 60 phút (refresh 30s) | total <= 50,000 tokens | `/metrics` → `tokens_in_total`, `tokens_out_total` |
| 6 | **Quality** | Quality proxy | `score_0_to_1` | 60 phút (refresh 30s) | mean >= 0.75 | `/metrics` → `quality_avg` |

**Công cụ sử dụng:** Mô tả bằng file định nghĩa cấu hình (`config/dashboard.yaml`).

**Evidence Dashboard:**
*(Thành viên 3 đính kèm ảnh chụp màn hình dashboard - Grafana/Langfuse - hoặc lưu file đặc tả YAML này vào thư mục evidence)*
