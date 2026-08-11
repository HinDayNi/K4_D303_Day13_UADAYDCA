# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- **Tên nhóm:** UADAYDCA
- **Repository URL:** https://github.com/HinDayNi/K4_D303_Day13_UADAYDCA
- **Commit SHA cuối:** `[Chưa cập nhật — điền SHA của commit cuối trước khi nộp]`
- **Thành viên và vai trò:**

| Thành viên | Vai trò | Phạm vi chính |
|---|---|---|
| Trần Thị Hương | Logging & PII Owner | JSON logging, correlation ID, metadata và PII redaction |
| Nguyễn Thị Thanh Hiền | Tracing & Prompt Versioning Owner | Traces, metadata, prompt v1/v2, label và rollback |
| Nguyễn Công Việt Quang | Metrics, Dashboard, SLO & Alerts Owner | Dashboard 6 panel, SLO, threshold, alert rules và runbook |
| Đỗ Thành Đạt | Incident, Integration, Report & Demo Lead | Điều tra challenge, tích hợp, evidence, báo cáo và demo cuối |

## 2. Kết quả kỹ thuật

- **Điểm `validate_logs.py`:** `[Chưa cập nhật]`
- **Tổng số traces:** `[Chưa cập nhật — yêu cầu tối thiểu 10]`
- **Số PII leak còn lại:** `[Chưa cập nhật — mục tiêu 0]`
- **Link/đường dẫn dashboard:** `[Chưa cập nhật]`

## 3. Logging và tracing

- **Evidence correlation ID:** `[Chưa cập nhật]`
- **Evidence PII redaction:** `[Chưa cập nhật]`
- **Evidence trace waterfall:** `[Chưa cập nhật]`
- **Giải thích một span đáng chú ý:** `[Chưa cập nhật]`

## 4. Prompt versioning

- **Prompt name:** `day13-chat`
- **Version/label baseline:** `[Chưa cập nhật]`
- **Version/label candidate:** `[Chưa cập nhật]`
- **Trace ID của mỗi version:** `[Chưa cập nhật]`
- **Bằng chứng đổi label hoặc rollback:** `[Chưa cập nhật]`

## 5. Dashboard, SLO và alerts

- **Kết quả `validate_dashboard.py`:** `[Chưa cập nhật — mục tiêu 6/6 panel hợp lệ]`
- **Evidence dashboard:** `[Chưa cập nhật]`
- **SLO đã chọn và lý do:** `[Chưa cập nhật]`
- **Alert rules và runbook:** `[Chưa cập nhật]`

## 6. Điều tra challenge

- **Challenge ID:** `[Chưa cập nhật sau khi Lab Coach release challenge]`
- **Triệu chứng từ metrics:** `[Chưa cập nhật]`
- **Trace ID liên quan:** `[Chưa cập nhật]`
- **Log line/correlation ID liên quan:** `[Chưa cập nhật]`
- **Root cause:** `[Chưa cập nhật]`
- **Fix action:** `[Chưa cập nhật]`
- **Preventive measure:** `[Chưa cập nhật]`

## 7. Đóng góp cá nhân

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| Trần Thị Hương | Logging & PII | `[Chưa cập nhật]` | `[Chưa cập nhật]` |
| Nguyễn Thị Thanh Hiền | Tracing & Prompt Versioning | `[Chưa cập nhật]` | `[Chưa cập nhật]` |
| Nguyễn Công Việt Quang | Metrics, Dashboard, SLO & Alerts | `[Chưa cập nhật]` | `[Chưa cập nhật]` |
| Đỗ Thành Đạt | Incident, Integration, Report & Demo | `[Chưa cập nhật]` | `[Chưa cập nhật]` |

## 8. Kịch bản demo

1. **Metrics:** trình bày triệu chứng và khoảng thời gian bất thường — `[Người trình bày: Nguyễn Công Việt Quang]`.
2. **Traces:** mở trace và khoanh vùng span bất thường — `[Người trình bày: Nguyễn Thị Thanh Hiền]`.
3. **Logs:** truy theo correlation ID, chứng minh root cause và PII đã được che — `[Người trình bày: Trần Thị Hương]`.
4. **Root cause và hành động:** kết luận root cause, fix action, preventive measure và tổng kết — `[Người trình bày: Đỗ Thành Đạt]`.

## 9. Kiểm tra trước khi nộp

- [ ] `python -m pytest -q` chạy đạt.
- [ ] `python scripts/validate_logs.py` đạt tối thiểu 80/100.
- [ ] `python scripts/validate_dashboard.py` báo hợp lệ.
- [ ] Có tối thiểu 10 traces và đủ evidence bắt buộc trong `submission/evidence/`.
- [ ] Không có secret, `.env` hoặc PII chưa redact trong Git.
- [ ] Các commit/PR khớp với khai báo đóng góp cá nhân.
- [ ] Đã cập nhật commit SHA cuối và kiểm tra repository URL clone được.
