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


CHUNK = 100


def fetch_prices(tickers: list[str]) -> tuple[dict, list[str]]:
    """Last close per ticker, fetched in batches.

    One request per hundred symbols rather than one per symbol -- with a
    five-hundred-name list the per-symbol approach is slow enough to get
    rate-limited, and a rate-limited run looks exactly like a delisted ticker.
    """
    import yfinance as yf

    prices: dict[str, float] = {}
    missing: list[str] = []
    if not tickers:
        return prices, missing

    for i in range(0, len(tickers), CHUNK):
        batch = tickers[i:i + CHUNK]
        try:
            df = yf.download(batch, period="5d", interval="1d",
                             group_by="ticker", auto_adjust=False,
                             progress=False, threads=True)
        except Exception as exc:                     # noqa: BLE001
            print(f"::warning::batch {i // CHUNK + 1} failed: "
                  f"{type(exc).__name__}: {exc}")
            missing.extend(batch)
            continue

        for t in batch:
            try:
                # yfinance returns a flat frame for one symbol, a MultiIndex
                # for several.
                close = df["Close"] if len(batch) == 1 else df[t]["Close"]
                close = close.dropna()
                if close.empty:
                    raise ValueError("no close in the window")
                prices[t] = round(float(close.iloc[-1]), 4)
            except Exception:                        # noqa: BLE001
                missing.append(t)

    if missing:
        print(f"::warning::no price for {len(missing)} symbol(s): "
              f"{', '.join(missing[:20])}"
              f"{' …' if len(missing) > 20 else ''}")
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
