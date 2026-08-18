#!/usr/bin/env python3
"""Fetch prices and index history, write docs/data/market.json.

Runs in GitHub Actions on a schedule. Because it runs server-side there is no
CORS problem and no API key: yfinance talks to Yahoo directly, and the result
is committed next to the page, where the browser can read it same-origin.

Tickers come from docs/data/tickers.json so the page owner edits one small
file instead of touching this script.
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "docs" / "data" / "tickers.json"
OUT = ROOT / "docs" / "data" / "market.json"

DEFAULT_CONFIG = {
    "benchmark": "SPY",
    "benchmarkName": "S&P 500",
    "tickers": ["VOO", "SCHD", "AAPL", "NVDA", "FXAIX"],
    "historyYears": 8,
}


def load_config() -> dict:
    if CONFIG.exists():
        try:
            cfg = json.loads(CONFIG.read_text())
            return {**DEFAULT_CONFIG, **cfg}
        except json.JSONDecodeError as exc:
            print(f"::warning::{CONFIG.name} is not valid JSON ({exc}); using defaults")
    return dict(DEFAULT_CONFIG)


def fetch_prices(tickers: list[str]) -> tuple[dict, list[str]]:
    import yfinance as yf

    prices, missing = {}, []
    if not tickers:
        return prices, missing
    data = yf.Tickers(" ".join(tickers))
    for t in tickers:
        try:
            fi = data.tickers[t].fast_info
            px = fi.get("lastPrice") or fi.get("last_price")
            if px is None:
                raise ValueError("no lastPrice")
            prices[t] = round(float(px), 4)
        except Exception as exc:                     # noqa: BLE001
            missing.append(t)
            print(f"::warning::no price for {t}: {type(exc).__name__}: {exc}")
    return prices, missing


def fetch_benchmark(symbol: str, years: int) -> list[dict]:
    import yfinance as yf

    start = date.today().replace(year=date.today().year - years)
    hist = yf.Ticker(symbol).history(start=start.isoformat(), interval="1mo")
    out = []
    for stamp, row in hist.iterrows():
        close = row.get("Close")
        if close is None or close != close:          # NaN guard
            continue
        out.append({"m": stamp.strftime("%Y-%m"), "c": round(float(close), 2)})
    # de-duplicate, keeping the last close seen for a month
    merged: dict[str, float] = {}
    for row in out:
        merged[row["m"]] = row["c"]
    return [{"m": m, "c": merged[m]} for m in sorted(merged)]


def main() -> int:
    cfg = load_config()
    tickers = sorted({t.upper().strip() for t in cfg["tickers"] if t.strip()})
    bench = cfg["benchmark"].upper().strip()

    prices, missing = fetch_prices(tickers)
    try:
        series = fetch_benchmark(bench, int(cfg["historyYears"]))
    except Exception as exc:                          # noqa: BLE001
        print(f"::error::benchmark fetch failed: {exc}")
        series = []

    if not prices and not series:
        print("::error::nothing fetched; leaving the existing file alone")
        return 1

    payload = {
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "benchSymbol": bench,
        "benchName": cfg["benchmarkName"],
        "prices": prices,
        "benchmark": series,
        "missing": missing,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=1) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(prices)} prices, "
          f"{len(series)} months of {bench}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
