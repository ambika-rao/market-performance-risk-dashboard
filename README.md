# Market Performance & Risk Analysis Dashboard

A Python project that downloads historical stock data, computes six quantitative risk and return metrics, generates four publication-quality charts, and produces a ranked summary table — all from a single command.

Built as a portfolio project demonstrating applied quantitative finance and software engineering skills.

---

## Features

- Downloads and caches historical adjusted closing prices via `yfinance`
- Computes six financial metrics per ticker: annualized return, annualized volatility, Sharpe ratio, maximum drawdown, cumulative return, and rolling volatility
- Generates four charts saved as high-resolution PNGs
- Prints a ranked terminal table sorted by Sharpe ratio and exports results to CSV
- 34 unit tests covering every calculation function, each verifiable by hand from the underlying formula

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/market-performance-risk-dashboard.git
cd market-performance-risk-dashboard

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate          # macOS / Linux
venv\Scripts\activate             # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the dashboard
python main.py
```

That's it. Charts are saved to `outputs/charts/` and CSV files to `outputs/data/`.

To analyze different stocks or a different time period, open `config.py` and change `TICKERS`, `START_DATE`, or `END_DATE` — then re-run `python main.py`.

---

## Configuration

All project settings live in one file: [`config.py`](config.py). Nothing is hardcoded anywhere else.

| Setting | Default | Description |
|---|---|---|
| `TICKERS` | `["AAPL", "MSFT", "SPY", "NVDA"]` | Any valid Yahoo Finance ticker symbols |
| `START_DATE` | `"2019-01-01"` | Start of historical data window |
| `END_DATE` | `"2024-12-31"` | End of historical data window |
| `RISK_FREE_RATE` | `0.043` | Annual risk-free rate (4.3% ≈ 2024 3-month T-bill) |
| `ROLLING_WINDOW` | `30` | Trading days for rolling volatility window |

---

## Sample Output

Running with the default configuration (AAPL, MSFT, SPY, NVDA over 2019–2024):

```
=======================================================================
  PERFORMANCE & RISK SUMMARY  (sorted by Sharpe Ratio, best first)
=======================================================================
| Rank | Ticker | Ann. Return (%) | Ann. Volatility (%) | Sharpe Ratio | Max Drawdown (%) | Total Cum. Return (%) |
|------|--------|-----------------|---------------------|--------------|------------------|-----------------------|
|    1 | NVDA   |          112.24 |               51.89 |         2.08 |           -66.34 |               3970.05 |
|    2 | AAPL   |           44.06 |               30.85 |         1.29 |           -31.43 |                568.81 |
|    3 | MSFT   |           33.88 |               29.00 |         1.02 |           -37.15 |                345.73 |
|    4 | SPY    |           19.53 |               19.84 |         0.77 |           -33.72 |                158.40 |
=======================================================================
```

Notable finding: NVDA delivered the highest raw return (112% annualized) but also the worst drawdown (-66%), meaning an investor who bought at the 2021 peak lost two-thirds of their investment before recovering. SPY had the lowest Sharpe ratio but the smallest peak-to-trough decline — consistent with the role of a diversified index in a portfolio.

---

## Charts

| Chart | What it shows |
|---|---|
| `price_history.png` | Raw adjusted closing prices over time. Useful for spotting trends but limited for cross-ticker comparison since prices have different scales. |
| `cumulative_returns.png` | Growth of $1 invested at the start date. Puts all tickers on the same baseline — the standard "horse race" comparison used in fund fact sheets. |
| `return_distribution.png` | Histogram of daily returns per ticker. Reveals the shape of risk: fat tails, skewness, and the frequency of extreme days. |
| `rolling_volatility.png` | 30-day rolling annualized volatility. Shows *when* risk spiked (e.g. March 2020 COVID crash) rather than just the static average. |

---

## Metrics Explained

### Annualized Return
The average daily return compounded over a full trading year (252 days).

```
Annualized Return = (1 + mean_daily_return)^252 − 1
```

**Why it matters:** Converts any time period's performance into a common yearly scale, making cross-ticker and cross-period comparisons fair.

---

### Annualized Volatility
The standard deviation of daily returns, scaled to a yearly figure.

```
Annualized Volatility = std(daily_returns) × √252
```

**Why √252?** Variance scales linearly with time; standard deviation scales with the square root of time. This is the same square-root-of-time rule used in actuarial risk models and VaR calculations.

**Why it matters:** This is the standard definition of market risk. A stock with 50% annualized volatility swings far more than one with 20% — even if both have the same average return.

---

### Sharpe Ratio
Return earned above the risk-free rate, per unit of risk taken.

```
Sharpe Ratio = (Annualized Return − Risk-Free Rate) / Annualized Volatility
```

**Why it matters:** Created by Nobel laureate William Sharpe, this is the most widely used risk-adjusted performance metric in portfolio management. A Sharpe above 1.0 is generally considered good; above 2.0 is very good. It answers the question every rational investor should ask: *"Am I being paid enough for the risk I'm taking?"*

| Sharpe | Interpretation |
|---|---|
| < 0 | Return is below the risk-free rate |
| 0 – 1 | Suboptimal risk-adjusted return |
| 1 – 2 | Good |
| 2 – 3 | Very good |
| > 3 | Excellent (rare over long periods) |

---

### Maximum Drawdown
The largest percentage decline from any historical peak to a subsequent trough.

```
Drawdown_t  = (Wealth_t − RunningMax_t) / RunningMax_t
Max Drawdown = min(Drawdown_t)
```

**Why it matters:** Average return and volatility don't capture the worst single loss an investor experienced. Max drawdown answers a very human question: *"At the worst possible moment, how much of my money was I down from the top?"* Large drawdowns are the primary driver of panic selling at market bottoms.

---

### Rolling Volatility
Annualized volatility calculated over a moving 30-day window, producing a time series instead of a single number.

**Why it matters:** Risk is not constant — it has regimes. The rolling volatility chart typically reveals dramatic spikes during known stress events (COVID crash, 2022 rate hikes) that a single-number volatility figure would completely hide.

---

## Project Structure

```
market-performance-risk-dashboard/
│
├── main.py                  # Entry point — run this file to generate everything
├── config.py                # All settings in one place (tickers, dates, rf rate)
├── requirements.txt         # Pip-installable dependencies
│
├── src/
│   ├── data_fetcher.py      # Downloads and caches price data from Yahoo Finance
│   ├── metrics.py           # Six financial metric calculations (pure functions)
│   ├── visualizer.py        # Four chart generators, saved as PNG
│   └── reporter.py          # Summary table builder and CSV exporter
│
├── tests/
│   └── test_metrics.py      # 34 unit tests for every calculation function
│
└── outputs/                 # Auto-populated when you run main.py
    ├── charts/              # price_history.png, cumulative_returns.png, etc.
    └── data/                # summary_metrics.csv, daily_returns.csv
```

### Data flow

```
config.py ──── settings ──────────────────────────────────────────────────────┐
                                                                               │
main.py                                                                        │
  │                                                                            │
  ├── data_fetcher.py  →  prices DataFrame  ─────────────────────────────┐    │
  │                                                                       │    │
  ├── metrics.py       ←  prices            →  results dict              │    │
  │                                                                       │    │
  ├── visualizer.py    ←  prices + results + config  →  4 PNG files      │    │
  │                                                                       │    │
  └── reporter.py      ←  results + config           →  terminal table + 2 CSVs
```

Each module has exactly one responsibility. Changing the data source only touches `data_fetcher.py`. Changing a chart style only touches `visualizer.py`. Changing a metric formula only touches `metrics.py` — and the tests catch any unintended side effects immediately.

---

## Running the Tests

```bash
python -m unittest discover -s tests -v
```

Expected output: **34 tests in ~0.01 seconds, all passing.**

The tests are organized into one class per function (8 classes total) and cover three categories for each:
1. **Known input → known output** — every expected value is derivable by hand from the formula
2. **Boundary case** — zero returns, constant prices, always-rising series
3. **Invariant** — properties that must always hold (drawdown ≤ 0, volatility ≥ 0, compounding ≠ additive)

---

## Tech Stack

| Library | Version | Purpose |
|---|---|---|
| `yfinance` | 0.2.54 | Yahoo Finance data download |
| `pandas` | 2.2.3 | DataFrames, time-series operations |
| `numpy` | 2.2.3 | Vectorized math (sqrt, cumprod) |
| `matplotlib` | 3.10.1 | Chart rendering |
| `seaborn` | 0.13.2 | Color palettes and histogram styling |
| `tabulate` | 0.9.0 | Terminal table formatting |

No paid data subscriptions required. All price data is free via Yahoo Finance.

---

## Potential Extensions

Features that would meaningfully extend the project:

- **Value at Risk (VaR)** — estimate the maximum expected loss over one day at 95% confidence using the historical simulation method; a staple of every trading desk risk report
- **Correlation heatmap** — visualize how each pair of stocks moves together; critical for understanding diversification benefits and portfolio construction
- **Beta vs. benchmark** — measure each stock's sensitivity to S&P 500 moves; standard input for equity research reports and the CAPM framework
- **Sortino ratio** — a Sharpe variant that only penalizes downside volatility, not upside swings; preferred by many practitioners over the standard Sharpe
- **CLI interface** — accept tickers and dates as command-line arguments (`python main.py --tickers AAPL MSFT --start 2020-01-01`) using Python's `argparse` module
- **Interactive charts** — replace matplotlib with Plotly to produce HTML charts that can be embedded in a portfolio website

---

## Author

Built by a Mathematics of Finance and Actuarial Science student at NJIT as a demonstration of applied quantitative finance skills in Python.
