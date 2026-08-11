from __future__ import annotations

import hashlib
import re

# Bộ mẫu PII: mỗi khóa là loại dữ liệu nhạy cảm cần che trước khi log/trace.
# Thứ tự quan trọng: thẻ tín dụng trước CCCD để chuỗi 16 số không bị cắt nhầm thành 12 số CCCD.
PII_PATTERNS: dict[str, str] = {
    # Email trong tin nhắn/payload → thay bằng token cố định, giữ ngữ cảnh câu.
    "email": r"[\w\.-]+@[\w\.-]+\.\w+",
    # SĐT VN (+84 hoặc 0, có/không khoảng trắng/chấm/gạch) → che trước khi ghi log.
    "phone_vn": r"(?<!\d)(?:\+84|0)(?:[ .-]?\d){9}(?!\d)",
    # Số thẻ thử nghiệm 16 chữ số (kèm phân tách tùy chọn) → không để nguyên văn trong log.
    "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
    # CCCD/CMND 12 chữ số đứng độc lập → hash không dùng ở đây, chỉ redact token.
    "cccd": r"\b\d{12}\b",
    # Hộ chiếu VN dạng 1 chữ cái + 7 chữ số (vd. B1234567) → coi là định danh cá nhân.
    "passport": r"\b[A-Z]\d{7}\b",
    # Đoạn địa chỉ VN (có/không dấu) gắn từ khóa hành chính + phần theo sau → giảm lộ chỗ ở.
    "address_vn": (
        r"(?i)\b(?:số\s*nhà|so\s*nha|đường|duong|phố|pho|phường|phuong|xã|xa|"
        r"quận|quan|huyện|huyen|tỉnh|tinh|thành\s*phố|thanh\s*pho)"
        r"\s+[^,;.\n]{2,80}"
    ),
}


def scrub_text(text: str) -> str:
    # Đầu vào rỗng/None-like: không có PII để xử lý, trả nguyên trạng an toàn.
    if not text:
        return text

    # Duyệt từng loại PII trên cùng một chuỗi: mỗi lần khớp bị thay bằng [REDACTED_<LOẠI>].
    # Output cuối cùng là bản đã làm sạch, sẵn sàng đưa vào payload log hoặc preview.
    safe = text
    for name, pattern in PII_PATTERNS.items():
        safe = re.sub(pattern, f"[REDACTED_{name.upper()}]", safe)
        print(f"[Scrubbed] {name}: {safe}")  # Debug: log từng bước scrub PII
    return safe


def summarize_text(text: str, max_len: int = 80) -> str:
    # Preview cho log/trace: scrub trước, rồi rút gọn để không đẩy full message vào disk.
    safe = scrub_text(text).strip().replace("\n", " ")
    return safe[:max_len] + ("..." if len(safe) > max_len else "")


def hash_user_id(user_id: str) -> str:
    # user_id thô không được ghi log: chỉ giữ fingerprint 12 hex để correlate theo người dùng.
    return hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:12]
