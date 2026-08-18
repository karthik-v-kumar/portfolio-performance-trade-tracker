# Portfolio Performance & Trade Tracker

A single-page console for tracking investment accounts, holdings, and trades —
and answering the one question most portfolio trackers avoid:

> **Is picking your own stocks actually beating the index, or would you have
> done just as well buying the whole market and going outside?**

No install, no account, no server. One HTML file that runs in a browser and
keeps your data in that browser's local storage. Optionally, a bundled GitHub
Action keeps market prices up to date on a schedule so you never touch it again.

**[Live demo →](https://karthik-v-kumar.github.io/portfolio-performance-trade-tracker/)**
Opens with sample data. Erase it and enter your own whenever you like.

---

## What it does

**Dashboard.** Eight years of combined account value, with a second line
showing what the *same starting balance and the same deposits* would be worth
in the S&P 500. Deposits are separated from performance, so money you paid in
never masquerades as skill. Below that: total value, unrealized and realized
P&L, and a per-account breakdown.

**Holdings.** Lot-level tracking. Every purchase keeps its own date, quantity,
and cost, so average cost and unrealized gain are derived rather than typed.

**Trades.** Open positions with live P&L, R multiples, and stop/target
distance. Closing a trade moves it to history — it is never deleted.

**Performance.** Win rate, average hold, profit factor, average R, and P&L by
ticker. Then every closed trade is scored against the index over *its own
holding window*, weighted by the money actually at risk. That is a harsher test
than comparing annual returns, and it is the one that tells you whether the
picking is paying.

**Planner.** Compounding projections with contributions, expense-ratio drag,
and dividends reinvested or taken as cash. Compare funds side by side and see
what fees cost over decades. Pre-tax only, deliberately — see below.

### The part most trackers leave out

A win rate is only honest if losing trades get closed as promptly as winning
ones. The classic failure is logging winners immediately and letting losers sit
"open" so they never reach the denominator.

So the exit date is stamped when you record the close, and the console compares
that stamp against the sale date you entered. It reports your average logging
delay **split by winners and losers**, flags trades left open past your chosen
horizon, and shows what your win rate becomes if every stalled trade turns out
badly. The gap is measured rather than self-reported.

It also flags a ticker held in both a taxable account and an IRA or 401(k):
selling at a loss in the taxable account while a retirement account buys the
same security within 30 days permanently disallows the loss instead of
deferring it.

---

## How market data stays current

This is the part worth explaining, because a static page cannot fetch prices on
its own. Browsers block cross-origin requests unless the far end opts in, and
the free market-data endpoints do not. So the work happens **before** the page
loads, not during.

```
 GitHub Actions (scheduled)          your repo              the page
 ┌──────────────────────────┐      ┌──────────────┐      ┌──────────────┐
 │ scripts/fetch_market.py  │─────▶│ docs/data/   │─────▶│ fetch()      │
 │ yfinance, server-side:   │commit│ market.json  │ same │ same-origin, │
 │ no CORS, no API key      │      │              │origin│ always works │
 └──────────────────────────┘      └──────────────┘      └──────────────┘
        runs on a cron              served by Pages        merges on load
```

A scheduled workflow runs `yfinance` on GitHub's runners — server-side, where
CORS does not apply and no API key is needed — and commits the result to
`docs/data/market.json`. GitHub Pages serves that file from the same origin as
the page, so the browser can read it with a plain `fetch`. On load the app
merges in the new prices and index history, and (if you leave the setting on)
records this month's total value automatically.

After setup there is nothing to maintain. Prices, index history, and your
monthly value snapshot all update themselves.

**Three levels of automation**, in the order the app tries them:

| | How | Needs |
|---|---|---|
| **Automatic** | Bundled GitHub Action writes `market.json`; the page reads it | One-time setup below |
| **On demand** | Paste a free API key (Finnhub, Twelve Data, Alpha Vantage) into Setup and press *Fetch now* | A free key; won't work in sandboxed previews |
| **Manual** | Type a price, or paste a month-end column | Nothing |

### One-time setup

1. Fork or clone this repo.
2. **Settings → Pages** → *Deploy from a branch*, branch `main`, folder `/docs`.
3. **Settings → Actions → General** → *Workflow permissions* → **Read and write**
   (the workflow commits the data file).
4. Edit `docs/data/tickers.json` with the symbols you hold:

   ```json
   { "benchmark": "SPY", "benchmarkName": "S&P 500",
     "historyYears": 8, "tickers": ["VOO", "SCHD", "AAPL"] }
   ```

5. **Actions → Update market data → Run workflow** to prime it. After that it
   runs weekdays after the close.

The schedule lives in `.github/workflows/market-data.yml`; change the cron if
you want a different cadence. GitHub may pause scheduled workflows on repos
with no activity for 60 days — a single commit re-enables them.

---

## Your data

Everything you enter is kept in your browser's local storage on your own
device. Nothing is transmitted anywhere: there is no backend, no analytics, and
no account. The published data file flows one way, into the page.

That also means clearing site data erases it, so **Setup → Export backup**
writes a JSON file you can keep. Import restores it on any device.

Any API key you enter is stored the same way — in your browser only. It is
never committed, and never sent anywhere except to the provider you chose.

---

## Deliberately not included

**No tax calculations.** No cost-basis-to-tax-bill math, no bracket logic, no
after-tax projections. Tax treatment depends on details this app has no
business guessing at, and a number that looks authoritative but is wrong is
worse than no number. The one place tax is mentioned — the taxable/retirement
overlap flag — names a rule so you can look it up, and computes nothing.

**Not investment advice.** It reports arithmetic on numbers you supply. Sample
data is fictional and chosen to demonstrate the interface, including a track
record that slightly *trails* the index — because that is the outcome most
worth being able to see.

---

## Running it locally

The app is one self-contained file. Open `docs/index.html` in a browser and it
works — except for the automatic data feed, which needs a real origin:

```bash
python3 -m http.server 8000 --directory docs
# then open http://localhost:8000
```

To refresh the data file yourself:

```bash
pip install yfinance
python scripts/fetch_market.py
```

### Add it to a phone or dock

Open the page in Safari or Chrome and choose *Add to Home Screen* (iOS) or
*Install* (desktop Chrome). It picks up its own icon and opens without browser
chrome.

---

## Layout

```
docs/index.html              the whole app — markup, styles, logic, icons
docs/data/tickers.json       symbols the workflow fetches (edit this)
docs/data/market.json        written by the workflow, read by the page
scripts/fetch_market.py      yfinance → market.json
.github/workflows/           the schedule
```

No build step, no dependencies, no framework. The page is plain HTML, CSS, and
JavaScript so that it still opens in ten years.

## Licence

MIT — see [LICENSE](LICENSE).
