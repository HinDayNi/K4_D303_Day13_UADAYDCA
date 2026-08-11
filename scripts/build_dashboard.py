"""Dựng dashboard 6 panel từ data/logs.jsonl theo contract config/dashboard.yaml."""

from __future__ import annotations

import argparse
import html
import json
import sys
import webbrowser
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.cli import configure_utf8_stdio
from app.metrics import percentile

PALETTE = {
    "light": {
        "surface": "#fcfcfb", "plane": "#f9f9f7", "ink": "#0b0b0b", "ink2": "#52514e",
        "muted": "#898781", "grid": "#e1e0d9", "axis": "#c3c2b7",
        "border": "rgba(11,11,11,0.10)",
        "ord1": "#86b6ef", "ord2": "#2a78d6", "ord3": "#104281",
        "cat1": "#2a78d6", "cat2": "#eb6834",
        "good": "#0ca30c", "critical": "#d03b3b",
    },
    "dark": {
        "surface": "#1a1a19", "plane": "#0d0d0d", "ink": "#ffffff", "ink2": "#c3c2b7",
        "muted": "#898781", "grid": "#2c2c2a", "axis": "#383835",
        "border": "rgba(255,255,255,0.10)",
        "ord1": "#184f95", "ord2": "#3987e5", "ord3": "#cde2fb",
        "cat1": "#3987e5", "cat2": "#d95926",
        "good": "#0ca30c", "critical": "#d03b3b",
    },
}

PLOT = {"w": 720, "h": 200, "l": 56, "r": 18, "t": 14, "b": 32}


def load_records(log_path: Path) -> list[dict]:
    if not log_path.exists():
        raise SystemExit(f"Không tìm thấy {log_path}. Chạy API và load_test.py trước.")
    out = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def minute_key(ts: datetime) -> datetime:
    return ts.replace(second=0, microsecond=0)


PANEL_EVENTS = {"request_received", "request_failed", "response_sent"}


class Window:
    """Cửa sổ N phút cuối, neo vào request mới nhất để ảnh chụp luôn có dữ liệu.

    Chỉ neo vào PANEL_EVENTS: log vận hành như app_started sinh ra khi uvicorn
    --reload restart sẽ đẩy cửa sổ trôi khỏi vùng có traffic.
    """

    def __init__(self, records: list[dict], minutes: int) -> None:
        stamps = [
            ts
            for ts in (
                parse_ts(r.get("ts")) for r in records if r.get("event") in PANEL_EVENTS
            )
            if ts
        ]
        if not stamps:
            raise SystemExit("Log không có request nào. Chạy scripts/load_test.py trước.")
        self.end = max(stamps)
        self.start = self.end - timedelta(minutes=minutes)
        self.minutes = minutes
        self.buckets = [minute_key(self.start) + timedelta(minutes=i) for i in range(minutes + 1)]

    def contains(self, ts: datetime | None) -> bool:
        return ts is not None and self.start <= ts <= self.end

    @property
    def is_stale(self) -> bool:
        return (datetime.now(timezone.utc) - self.end) > timedelta(minutes=5)


def aggregate(records: list[dict], window: Window) -> dict:
    lat: dict[datetime, list[int]] = defaultdict(list)
    cost: dict[datetime, float] = defaultdict(float)
    tin: dict[datetime, int] = defaultdict(int)
    tout: dict[datetime, int] = defaultdict(int)
    qual: dict[datetime, list[float]] = defaultdict(list)
    traffic: dict[datetime, int] = defaultdict(int)
    failed: dict[datetime, int] = defaultdict(int)
    all_lat: list[int] = []
    error_types: Counter[str] = Counter()
    requests = errors = 0

    for rec in records:
        ts = parse_ts(rec.get("ts"))
        if not window.contains(ts):
            continue
        b = minute_key(ts)
        event = rec.get("event")
        if event == "request_received":
            traffic[b] += 1
            requests += 1
        elif event == "request_failed":
            failed[b] += 1
            errors += 1
            error_types[rec.get("error_type") or "unknown"] += 1
        elif event == "response_sent":
            if isinstance(rec.get("latency_ms"), (int, float)):
                lat[b].append(int(rec["latency_ms"]))
                all_lat.append(int(rec["latency_ms"]))
            cost[b] += float(rec.get("cost_usd") or 0)
            tin[b] += int(rec.get("tokens_in") or 0)
            tout[b] += int(rec.get("tokens_out") or 0)
            if isinstance(rec.get("quality_score"), (int, float)):
                qual[b].append(float(rec["quality_score"]))

    bs = window.buckets
    q_all = [v for values in qual.values() for v in values]
    return {
        "buckets": bs,
        "latency": {
            "p50": [percentile(lat[b], 50) if lat[b] else None for b in bs],
            "p95": [percentile(lat[b], 95) if lat[b] else None for b in bs],
            "p99": [percentile(lat[b], 99) if lat[b] else None for b in bs],
        },
        "p95_overall": percentile(all_lat, 95),
        "traffic": [traffic[b] for b in bs],
        "failed": [failed[b] for b in bs],
        "cost": [cost[b] for b in bs],
        "tokens_in": [tin[b] for b in bs],
        "tokens_out": [tout[b] for b in bs],
        "quality": [(sum(qual[b]) / len(qual[b])) if qual[b] else None for b in bs],
        "requests": requests,
        "errors": errors,
        "error_rate_pct": round(errors / requests * 100, 2) if requests else 0.0,
        "error_types": error_types,
        "cost_total": round(sum(cost.values()), 6),
        "tokens_in_total": sum(tin.values()),
        "tokens_out_total": sum(tout.values()),
        "quality_mean": round(sum(q_all) / len(q_all), 3) if q_all else 0.0,
        "rate_per_minute": round(requests / window.minutes, 2) if window.minutes else 0.0,
    }


def panels_by_id(config: dict) -> dict[str, dict]:
    return {p["id"]: p for p in config["dashboard"]["panels"]}


def status_of(value: float, panel: dict) -> str:
    th = panel["threshold"]
    ok = value <= th["value"] if th["operator"] == "lte" else value >= th["value"]
    return "ok" if ok else "breach"


def nice_max(value: float) -> float:
    if value <= 0:
        return 1.0
    exp = 10 ** (len(str(int(value))) - 1)
    for m in (1, 1.5, 2, 2.5, 3, 4, 5, 7.5, 10):
        if value <= exp * m:
            return exp * m
    return exp * 10


def fmt(value: float, unit: str) -> str:
    if unit == "usd":
        return f"${value:,.4f}" if value < 1 else f"${value:,.2f}"
    if unit == "percent":
        return f"{value:,.2f}%"
    if unit == "ms":
        return f"{value:,.0f} ms"
    if unit == "score_0_to_1":
        return f"{value:,.2f}"
    return f"{int(value):,}" if value == int(value) else f"{value:,.2f}"


def x_of(i: int, n: int) -> float:
    return PLOT["l"] + (PLOT["w"] - PLOT["l"] - PLOT["r"]) * i / max(1, n - 1)


def y_of(value: float, ymax: float) -> float:
    return PLOT["t"] + (PLOT["h"] - PLOT["t"] - PLOT["b"]) * (1 - (value / ymax if ymax else 0))


def bar_path(x: float, y: float, w: float, h: float, r: float = 4.0) -> str:
    r = min(r, w / 2, max(h, 0.1))
    bot = y + h
    return (
        f"M{x:.1f},{bot:.1f} L{x:.1f},{y + r:.1f} Q{x:.1f},{y:.1f} {x + r:.1f},{y:.1f} "
        f"L{x + w - r:.1f},{y:.1f} Q{x + w:.1f},{y:.1f} {x + w:.1f},{y + r:.1f} "
        f"L{x + w:.1f},{bot:.1f} Z"
    )


def chrome(ymax: float, buckets: list[datetime], unit: str) -> str:
    out = []
    for i in range(5):
        value = ymax * i / 4
        y = y_of(value, ymax)
        out.append(
            f'<line x1="{PLOT["l"]}" y1="{y:.1f}" x2="{PLOT["w"] - PLOT["r"]}" y2="{y:.1f}" '
            f'stroke="var(--grid)" stroke-width="1"/>'
            f'<text x="{PLOT["l"] - 8}" y="{y + 4:.1f}" text-anchor="end" class="tick">'
            f"{html.escape(fmt(value, unit))}</text>"
        )
    base = y_of(0, ymax)
    out.append(
        f'<line x1="{PLOT["l"]}" y1="{base:.1f}" x2="{PLOT["w"] - PLOT["r"]}" y2="{base:.1f}" '
        f'stroke="var(--axis)" stroke-width="1"/>'
    )
    n = len(buckets)
    for i in range(0, n, max(1, n // 6)):
        out.append(
            f'<text x="{x_of(i, n):.1f}" y="{PLOT["h"] - 10}" text-anchor="middle" '
            f'class="tick">{buckets[i].strftime("%H:%M")}</text>'
        )
    return "".join(out)


def threshold_line(value: float, ymax: float, label: str) -> str:
    if value > ymax:
        return ""
    y = y_of(value, ymax)
    return (
        f'<line x1="{PLOT["l"]}" y1="{y:.1f}" x2="{PLOT["w"] - PLOT["r"]}" y2="{y:.1f}" '
        f'stroke="var(--critical)" stroke-width="1.5" stroke-dasharray="6 4"/>'
        f'<text x="{PLOT["w"] - PLOT["r"]}" y="{y - 6:.1f}" text-anchor="end" '
        f'class="tick slo">{html.escape(label)}</text>'
    )


def line_series(values: list, ymax: float, var: str, name: str, unit: str) -> str:
    n = len(values)
    out: list[str] = []
    seg: list[str] = []

    def flush() -> None:
        if len(seg) > 1:
            out.append(
                f'<polyline points="{" ".join(seg)}" fill="none" stroke="var(--{var})" '
                f'stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>'
            )
        seg.clear()

    for i, value in enumerate(values):
        if value is None:
            flush()
        else:
            seg.append(f"{x_of(i, n):.1f},{y_of(value, ymax):.1f}")
    flush()

    for i, value in enumerate(values):
        if value is not None:
            out.append(
                f'<circle cx="{x_of(i, n):.1f}" cy="{y_of(value, ymax):.1f}" r="4" '
                f'fill="var(--{var})" stroke="var(--surface)" stroke-width="2">'
                f"<title>{html.escape(name)} · {html.escape(fmt(value, unit))}</title></circle>"
            )

    last = next((i for i in range(n - 1, -1, -1) if values[i] is not None), None)
    if last is not None:
        out.append(
            f'<text x="{x_of(last, n) - 8:.1f}" y="{y_of(values[last], ymax) - 10:.1f}" '
            f'text-anchor="end" class="endlabel">{html.escape(fmt(values[last], unit))}</text>'
        )
    return "".join(out)


def band_width(n: int) -> float:
    return min(24.0, max(2.0, (PLOT["w"] - PLOT["l"] - PLOT["r"]) / max(1, n) - 2))


def column_series(values: list, ymax: float, var: str, name: str, unit: str) -> str:
    n, w, base = len(values), band_width(len(values)), y_of(0, ymax)
    out = []
    for i, value in enumerate(values):
        if not value:
            continue
        y = y_of(value, ymax)
        out.append(
            f'<path d="{bar_path(x_of(i, n) - w / 2, y, w, base - y)}" fill="var(--{var})">'
            f"<title>{html.escape(name)} · {html.escape(fmt(value, unit))}</title></path>"
        )
    return "".join(out)


def stacked_series(lower: list[int], upper: list[int], ymax: float) -> str:
    n, w, base = len(lower), band_width(len(lower)), y_of(0, ymax)
    out = []
    for i in range(n):
        x = x_of(i, n) - w / 2
        if lower[i]:
            y = y_of(lower[i], ymax)
            out.append(
                f'<path d="{bar_path(x, y, w, base - y, r=0)}" fill="var(--cat1)">'
                f"<title>tokens_in · {lower[i]:,}</title></path>"
            )
        if upper[i]:
            y = y_of(lower[i] + upper[i], ymax)
            h = y_of(lower[i], ymax) - y - 2
            if h > 0.5:
                out.append(
                    f'<path d="{bar_path(x, y, w, h)}" fill="var(--cat2)">'
                    f"<title>tokens_out · {upper[i]:,}</title></path>"
                )
    return "".join(out)


def svg(body: str) -> str:
    return (
        f'<svg viewBox="0 0 {PLOT["w"]} {PLOT["h"]}" role="img" '
        f'preserveAspectRatio="xMidYMid meet">{body}</svg>'
    )


def legend(items: list[tuple[str, str]]) -> str:
    keys = "".join(
        f'<span class="key"><span class="swatch" style="background:var(--{v})"></span>'
        f"{html.escape(label)}</span>"
        for v, label in items
    )
    return f'<div class="legend">{keys}</div>'


def card(panel: dict, value: float, chart: str, legend_html: str = "", extra: str = "") -> str:
    th = panel["threshold"]
    state = status_of(value, panel)
    op = "≤" if th["operator"] == "lte" else "≥"
    return f"""
    <section class="card" id="panel-{panel['id']}">
      <header class="card-head">
        <div><h2>{html.escape(panel['title'])}</h2>
        <p class="sub">Đơn vị: {html.escape(panel['unit'])} · Ngưỡng: {th['aggregation']} {op}
        {html.escape(fmt(th['value'], panel['unit']))}</p></div>
        <span class="badge {state}">{'trong ngưỡng' if state == 'ok' else 'vượt ngưỡng'}</span>
      </header>
      {legend_html}
      <div class="plot">{chart}</div>{extra}
    </section>"""


def build_panels(config: dict, d: dict) -> str:
    p, bs = panels_by_id(config), d["buckets"]
    cards = []

    lat_all = [v for s in d["latency"].values() for v in s if v is not None]
    ymax = nice_max(max(lat_all + [p["latency"]["threshold"]["value"]], default=1))
    cards.append(card(
        p["latency"], d["p95_overall"],
        svg(chrome(ymax, bs, "ms")
            + threshold_line(p["latency"]["threshold"]["value"], ymax, "SLO p95 ≤ 3000 ms")
            + line_series(d["latency"]["p50"], ymax, "ord1", "p50", "ms")
            + line_series(d["latency"]["p95"], ymax, "ord2", "p95", "ms")
            + line_series(d["latency"]["p99"], ymax, "ord3", "p99", "ms")),
        legend([("ord1", "p50"), ("ord2", "p95"), ("ord3", "p99")]),
    ))

    ymax = nice_max(max(d["traffic"] + [1]))
    cards.append(card(
        p["traffic"], d["rate_per_minute"],
        svg(chrome(ymax, bs, "requests_per_minute")
            + threshold_line(p["traffic"]["threshold"]["value"], ymax, "Sàn ≥ 1 req/phút")
            + column_series(d["traffic"], ymax, "cat1", "Request", "requests_per_minute")),
    ))

    ymax = nice_max(max(d["failed"] + [1]))
    rows = "".join(
        f"<tr><td>{html.escape(name)}</td><td class='num'>{count:,}</td></tr>"
        for name, count in d["error_types"].most_common()
    ) or "<tr><td colspan='2' class='empty'>Không có request lỗi trong cửa sổ</td></tr>"
    cards.append(card(
        p["errors"], d["error_rate_pct"],
        svg(chrome(ymax, bs, "requests_per_minute")
            + column_series(d["failed"], ymax, "critical", "Lỗi", "requests_per_minute")),
        extra=f"""<p class="metric">Error rate <strong>{d['error_rate_pct']:.2f}%</strong>
        ({d['errors']:,}/{d['requests']:,} request)</p>
        <table><thead><tr><th>error_type</th><th class="num">Số lần</th></tr></thead>
        <tbody>{rows}</tbody></table>""",
    ))

    ymax = nice_max(max(d["cost"] + [0.001]))
    cards.append(card(
        p["cost"], d["cost_total"],
        svg(chrome(ymax, bs, "usd") + column_series(d["cost"], ymax, "cat1", "Chi phí", "usd")),
        extra=f"""<p class="metric">Tổng cửa sổ <strong>{fmt(d['cost_total'], 'usd')}</strong>
        / ngân sách {fmt(p['cost']['threshold']['value'], 'usd')}</p>""",
    ))

    totals = [a + b for a, b in zip(d["tokens_in"], d["tokens_out"])]
    ymax = nice_max(max(totals + [1]))
    cards.append(card(
        p["tokens"], max(d["tokens_in_total"], d["tokens_out_total"]),
        svg(chrome(ymax, bs, "tokens") + stacked_series(d["tokens_in"], d["tokens_out"], ymax)),
        legend([("cat1", "tokens_in"), ("cat2", "tokens_out")]),
        extra=f"""<p class="metric">tokens_in <strong>{d['tokens_in_total']:,}</strong> ·
        tokens_out <strong>{d['tokens_out_total']:,}</strong></p>""",
    ))

    cards.append(card(
        p["quality"], d["quality_mean"],
        svg(chrome(1.0, bs, "score_0_to_1")
            + threshold_line(p["quality"]["threshold"]["value"], 1.0, "SLO ≥ 0.75")
            + line_series(d["quality"], 1.0, "cat1", "quality", "score_0_to_1")),
    ))
    return "\n".join(cards)


def build_kpis(config: dict, d: dict) -> str:
    p = panels_by_id(config)
    tiles = [
        ("Latency p95", d["p95_overall"], p["latency"], "ms"),
        ("Request/phút", d["rate_per_minute"], p["traffic"], "requests_per_minute"),
        ("Error rate", d["error_rate_pct"], p["errors"], "percent"),
        ("Tổng chi phí", d["cost_total"], p["cost"], "usd"),
        ("Tokens out", d["tokens_out_total"], p["tokens"], "tokens"),
        ("Quality trung bình", d["quality_mean"], p["quality"], "score_0_to_1"),
    ]
    body = "".join(
        f'<a class="tile {status_of(v, panel)}" href="#panel-{panel["id"]}">'
        f'<span class="tile-label">{html.escape(label)}</span>'
        f'<span class="tile-value">{html.escape(fmt(v, unit))}</span></a>'
        for label, v, panel, unit in tiles
    )
    return f'<div class="kpis">{body}</div>'


def build_table(d: dict) -> str:
    rows = []
    for i, b in enumerate(d["buckets"]):
        if not (d["traffic"][i] or d["failed"][i] or d["latency"]["p95"][i]):
            continue
        p95 = d["latency"]["p95"][i]
        q = d["quality"][i]
        rows.append(
            f"<tr><td>{b.strftime('%H:%M')}</td>"
            f"<td class='num'>{d['traffic'][i]:,}</td>"
            f"<td class='num'>{d['failed'][i]:,}</td>"
            f"<td class='num'>{f'{p95:,.0f}' if p95 is not None else '–'}</td>"
            f"<td class='num'>{d['cost'][i]:.6f}</td>"
            f"<td class='num'>{d['tokens_in'][i]:,}</td>"
            f"<td class='num'>{d['tokens_out'][i]:,}</td>"
            f"<td class='num'>{f'{q:.2f}' if q is not None else '–'}</td></tr>"
        )
    body = "".join(rows) or "<tr><td colspan='8' class='empty'>Không có dữ liệu</td></tr>"
    return f"""
    <details class="tableview">
      <summary>Xem dạng bảng</summary>
      <div class="scroll"><table>
        <thead><tr><th>Phút</th><th class="num">Request</th><th class="num">Lỗi</th>
        <th class="num">p95 (ms)</th><th class="num">Cost (USD)</th><th class="num">tokens_in</th>
        <th class="num">tokens_out</th><th class="num">Quality</th></tr></thead>
        <tbody>{body}</tbody></table></div>
    </details>"""


def css() -> str:
    def vars_of(mode: str) -> str:
        return "".join(f"--{k}:{v};" for k, v in PALETTE[mode].items())

    return f"""
    :root {{ color-scheme: light; {vars_of("light")} }}
    @media (prefers-color-scheme: dark) {{
      :root:not([data-theme="light"]) {{ color-scheme: dark; {vars_of("dark")} }}
    }}
    :root[data-theme="dark"] {{ color-scheme: dark; {vars_of("dark")} }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; padding: 24px; background: var(--plane); color: var(--ink);
      font: 14px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }}
    .wrap {{ max-width: 1180px; margin: 0 auto; }}
    h1 {{ font-size: 22px; margin: 0 0 4px; }}
    .meta {{ color: var(--ink2); margin: 0 0 4px; }}
    .meta code {{ color: var(--ink); }}
    .stale {{ color: var(--critical); font-weight: 600; }}
    .kpis {{ display: grid; gap: 12px; margin: 20px 0;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); }}
    .tile {{ display: flex; flex-direction: column; gap: 6px; padding: 14px 16px;
      border-radius: 10px; text-decoration: none; background: var(--surface);
      border: 1px solid var(--border); border-left: 3px solid var(--good); color: inherit; }}
    .tile.breach {{ border-left-color: var(--critical); }}
    .tile-label {{ color: var(--ink2); font-size: 12px; }}
    .tile-value {{ font-size: 24px; font-weight: 600; }}
    .grid {{ display: grid; gap: 16px;
      grid-template-columns: repeat(auto-fit, minmax(460px, 1fr)); }}
    .card {{ background: var(--surface); border: 1px solid var(--border);
      border-radius: 10px; padding: 16px; scroll-margin-top: 16px; }}
    .card-head {{ display: flex; justify-content: space-between; align-items: start; gap: 12px; }}
    .card h2 {{ font-size: 15px; margin: 0; }}
    .sub {{ color: var(--muted); font-size: 12px; margin: 4px 0 0; }}
    .badge {{ font-size: 11px; padding: 3px 8px; border-radius: 999px; white-space: nowrap;
      border: 1px solid var(--good); color: var(--ink2); }}
    .badge.breach {{ border-color: var(--critical); color: var(--critical); font-weight: 600; }}
    .legend {{ display: flex; gap: 14px; flex-wrap: wrap; margin: 10px 0 0; }}
    .key {{ display: inline-flex; align-items: center; gap: 6px; font-size: 12px;
      color: var(--ink2); }}
    .swatch {{ width: 10px; height: 10px; border-radius: 2px; }}
    .plot {{ margin-top: 8px; }}
    .plot svg {{ width: 100%; height: auto; display: block; }}
    .tick {{ fill: var(--muted); font-size: 10px; font-variant-numeric: tabular-nums; }}
    .slo {{ fill: var(--critical); }}
    .endlabel {{ fill: var(--ink2); font-size: 11px; font-weight: 600; }}
    .metric {{ margin: 10px 0 0; color: var(--ink2); font-size: 13px; }}
    .metric strong {{ color: var(--ink); }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 10px; font-size: 12px; }}
    th, td {{ padding: 5px 8px; border-bottom: 1px solid var(--grid); text-align: left; }}
    th {{ color: var(--muted); font-weight: 500; }}
    .num {{ text-align: right; font-variant-numeric: tabular-nums; }}
    .empty {{ color: var(--muted); }}
    .tableview {{ margin-top: 18px; background: var(--surface); border: 1px solid var(--border);
      border-radius: 10px; padding: 14px 16px; }}
    .tableview summary {{ cursor: pointer; color: var(--ink2); }}
    .scroll {{ overflow-x: auto; }}
    footer {{ margin-top: 18px; color: var(--muted); font-size: 12px; }}"""


def render(config: dict, d: dict, window: Window, log_path: Path) -> str:
    dash = config["dashboard"]
    stale = (
        '<p class="meta stale">Bản ghi mới nhất đã quá 5 phút — chạy lại load test '
        "trước khi chụp evidence.</p>"
        if window.is_stale else ""
    )
    return f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="{dash['refresh_seconds']}">
<title>{html.escape(dash['title'])}</title>
<style>{css()}</style>
</head>
<body>
<div class="wrap">
  <h1>{html.escape(dash['title'])}</h1>
  <p class="meta">Cửa sổ {dash['time_range_minutes']} phút:
    <code>{window.start.strftime('%Y-%m-%d %H:%M')}</code> →
    <code>{window.end.strftime('%H:%M')} UTC</code>
    · refresh {dash['refresh_seconds']}s
    · nguồn <code>{html.escape(log_path.name)}</code>
    · {d['requests']:,} request</p>
  {stale}
  {build_kpis(config, d)}
  <div class="grid">
{build_panels(config, d)}
  </div>
  {build_table(d)}
  <footer>Ngưỡng và đơn vị đọc từ <code>config/dashboard.yaml</code>
  · kiểm tra bằng <code>python scripts/validate_dashboard.py</code></footer>
</div>
</body>
</html>"""


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=REPO_ROOT / "config" / "dashboard.yaml")
    parser.add_argument("--logs", type=Path, default=REPO_ROOT / "data" / "logs.jsonl")
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "data" / "dashboard.html")
    parser.add_argument("--minutes", type=int, default=None)
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args()

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    records = load_records(args.logs)
    minutes = args.minutes or config["dashboard"]["time_range_minutes"]
    window = Window(records, minutes)
    d = aggregate(records, window)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render(config, d, window, args.logs), encoding="utf-8")

    p = panels_by_id(config)
    print(f"Dashboard: {args.out}")
    print(
        f"Cửa sổ {minutes} phút: {window.start:%Y-%m-%d %H:%M} → {window.end:%H:%M} UTC"
        f" · {d['requests']} request"
    )
    for pid, value, unit in [
        ("latency", d["p95_overall"], "ms"),
        ("traffic", d["rate_per_minute"], "requests_per_minute"),
        ("errors", d["error_rate_pct"], "percent"),
        ("cost", d["cost_total"], "usd"),
        ("tokens", max(d["tokens_in_total"], d["tokens_out_total"]), "tokens"),
        ("quality", d["quality_mean"], "score_0_to_1"),
    ]:
        th = p[pid]["threshold"]
        state = "OK  " if status_of(value, p[pid]) == "ok" else "VƯỢT"
        op = "<=" if th["operator"] == "lte" else ">="
        print(f"  [{state}] {pid:<8}{fmt(value, unit):>14}  (ngưỡng {op} {fmt(th['value'], unit)})")

    if args.open:
        webbrowser.open(args.out.resolve().as_uri())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
