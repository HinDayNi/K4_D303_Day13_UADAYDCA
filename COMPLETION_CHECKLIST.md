# Checklist tiêu chí hoàn thành Day 13

Checklist này tổng hợp từ `CHECKPOINTS.md`, `SUBMISSION.md` và `RUBRIC.md`.

## 1. Điều kiện hợp lệ tối thiểu

- [ ] Repository có thể clone được từ URL sẽ nộp.
- [ ] Source hoàn chỉnh nằm trong `app/`, `config/`, `scripts/` và `tests/`.
- [ ] `submission/REPORT.md` đã được điền đầy đủ.
- [ ] Không commit `.env`, API key, secret, `.venv/`, cache hoặc dependency đã cài.
- [ ] Không có PII chưa che trong log hoặc lịch sử phần việc sẽ nộp.
- [ ] Không dùng source/ảnh từ sample solution của đội khác.
- [ ] Không tự ý sửa `config/challenge.json`.
- [ ] Tên repository tuân theo quy định Lab Coach (nếu có).
- [ ] Có URL repository và commit SHA cuối để nộp trên Codelabs.

> Thiếu report, repo không clone được, lộ secret hoặc nộp sai loại URL thì bài chưa hợp lệ và phải nộp lại.

## 2. Setup và baseline

- [ ] Hoàn tất setup theo `SETUP.md` (ưu tiên Langfuse chung/cloud; Docker local là tùy chọn).
- [ ] API chạy được.
- [ ] Load test chạy được.
- [ ] Có file `data/logs.jsonl`.
- [ ] Chạy `python scripts/validate_logs.py` và lưu kết quả baseline vào report.

## 3. Logging và bảo vệ PII — A1

- [ ] Log ở định dạng JSON đúng yêu cầu.
- [ ] Mỗi request có correlation ID hợp lệ.
- [ ] Log API có đủ `user_id_hash`, `session_id`, `feature`, `model`, `env`.
- [ ] Email thử nghiệm không xuất hiện nguyên văn trong log.
- [ ] Số điện thoại thử nghiệm không xuất hiện nguyên văn trong log.
- [ ] Số thẻ thử nghiệm không xuất hiện nguyên văn trong log.
- [ ] `python scripts/validate_logs.py` đạt ít nhất 80/100.
- [ ] Có evidence log chứa correlation ID.
- [ ] Có evidence chứng minh PII đã được redact.

## 4. Traces và prompt versioning — A1

- [ ] Có ít nhất 10 traces kèm metadata.
- [ ] Có một trace waterfall rõ ràng.
- [ ] Có prompt v1 và v2 theo `docs/PROMPT_VERSIONING.md`.
- [ ] Trace hiển thị đúng `prompt_name`, `prompt_label`, `prompt_version`.
- [ ] Đã thực hiện ít nhất một lần đổi label hoặc rollback prompt.
- [ ] Có evidence của hai prompt version và trace gắn đúng version/label.
- [ ] Có evidence thao tác đổi label hoặc rollback.

> Rubric không chấm chất lượng nội dung prompt; trọng tâm là version/label metadata và bằng chứng rollback.

## 5. Dashboard, SLO và vận hành — A1

- [ ] `python scripts/validate_dashboard.py` báo hợp lệ.
- [ ] Dashboard tuân theo `docs/DASHBOARD_SETUP.md` và `config/dashboard.yaml`.
- [ ] Dashboard có đủ 6 nhóm/panel chỉ số theo dashboard contract, bao phủ latency, traffic, error, token/cost và quality.
- [ ] Có SLO line hoặc threshold rõ ràng.
- [ ] Có alert rules hợp lý.
- [ ] Có runbook hợp lý.
- [ ] Có evidence kết quả dashboard validator.
- [ ] Có ảnh/evidence dashboard thể hiện đầy đủ các nhóm chỉ số yêu cầu.

## 6. Điều tra challenge/incident — A2

- [ ] Chỉ bắt đầu challenge chính thức sau khi Lab Coach release `config/challenge.json`.
- [ ] Chạy incident và input chính thức.
- [ ] Xác định đúng triệu chứng từ metrics.
- [ ] Dùng trace để khoanh vùng span bất thường.
- [ ] Dùng log để chứng minh root cause.
- [ ] Trình bày được chuỗi điều tra `Metrics → Traces → Logs → Root cause`.
- [ ] Đề xuất fix action phù hợp.
- [ ] Đề xuất preventive measure phù hợp.
- [ ] Có đầy đủ evidence điều tra challenge trong `submission/evidence/`.

## 7. Report, evidence và Git

- [ ] `submission/REPORT.md` mô tả kết quả baseline.
- [ ] Report mô tả rõ phần việc của từng cá nhân.
- [ ] Khai báo đóng góp trong report khớp với thay đổi trong Git.
- [ ] `submission/evidence/` có kết quả `validate_logs.py`.
- [ ] `submission/evidence/` có danh sách ít nhất 10 traces.
- [ ] `submission/evidence/` có một trace waterfall.
- [ ] `submission/evidence/` có hai prompt version và trace tương ứng.
- [ ] `submission/evidence/` có bằng chứng đổi label/rollback prompt.
- [ ] `submission/evidence/` có log correlation ID và bằng chứng PII redaction.
- [ ] `submission/evidence/` có kết quả `validate_dashboard.py` và dashboard đủ yêu cầu.
- [ ] `submission/evidence/` có bằng chứng điều tra challenge.
- [ ] Mỗi thành viên có commit/PR cụ thể, kiểm tra được.
- [ ] Toàn bộ phần việc hợp lệ đã được commit.

## 8. Demo và hiểu bài — A3, B1

- [ ] Hệ thống chạy được trong buổi chấm.
- [ ] Demo ngắn đi theo luồng `Metrics → Traces → Logs → Root cause`.
- [ ] Nội dung demo khớp với evidence đã nộp.
- [ ] Mỗi thành viên giải thích được phần mình triển khai.
- [ ] Mỗi thành viên trả lời được câu hỏi liên quan đến phần việc về logging, tracing, prompt version, PII, percentile và/hoặc alert.

## 9. Kiểm tra cuối trước khi nộp

- [ ] `python -m pytest -q` chạy đạt.
- [ ] `python scripts/validate_logs.py` chạy đạt và còn giữ ngưỡng tối thiểu 80/100.
- [ ] `python scripts/validate_dashboard.py` báo hợp lệ.
- [ ] `git status --short` không cho thấy file nhạy cảm, file thừa hoặc thay đổi chưa xử lý.
- [ ] Kiểm tra lần cuối Git không chứa secret hoặc PII.
- [ ] Push đúng repository và đúng commit SHA sẽ nộp.

## 10. Đối chiếu điểm rubric

- [ ] **A1 — 30 điểm:** logging/correlation/metadata/PII (10); traces và prompt version/rollback (10); dashboard 6 panel, SLO, alert, runbook (10).
- [ ] **A2 — 10 điểm:** xác định triệu chứng/root cause, chứng minh luồng điều tra, có fix và preventive measure.
- [ ] **A3 — 20 điểm:** hệ thống chạy, demo đúng evidence, thành viên giải thích được phần việc.
- [ ] **B1 — 20 điểm:** báo cáo rõ phần cá nhân và thể hiện hiểu các khái niệm liên quan.
- [ ] **B2 — 20 điểm:** commit/PR kiểm tra được và khớp khai báo trong report.
- [ ] **Bonus — tối đa 10 điểm (không bắt buộc):** cost optimization có before/after, automation hữu ích hoặc audit log riêng.

Điểm cuối: `min(100, điểm nhóm + điểm cá nhân + bonus)`. Điểm do `validate_logs.py` in ra chỉ là kiểm tra kỹ thuật nhanh, không phải điểm rubric cuối cùng.
