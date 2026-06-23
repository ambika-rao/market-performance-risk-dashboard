# ============================================================
# config.py
# Market Performance & Risk Analysis Dashboard
# ============================================================
# PURPOSE: This file is the single place where you control
# ALL project settings. Nothing in this file does calculations
# or draws charts — it only defines configuration.
#
# WHY THIS MATTERS: In professional codebases, you never
# hard-code settings (like ticker names or dates) directly
# inside your logic files. If you want to change the tickers
# you're analyzing, you change it HERE — not in five different
# files. This is called "separation of concerns."
# ============================================================


# ------------------------------------------------------------
# SECTION 1: Stock Tickers to Analyze
# ------------------------------------------------------------
# A ticker is the short symbol used to identify a stock on an
# exchange. AAPL = Apple, MSFT = Microsoft, SPY = S&P 500 ETF,
# NVDA = Nvidia.
#
# HOW TO CUSTOMIZE: Replace or add any valid Yahoo Finance
# ticker symbols. Keep the list between 3 and 8 tickers for
# readable charts.
# ------------------------------------------------------------

TICKERS = ["AAPL", "MSFT", "SPY", "NVDA"]


# ------------------------------------------------------------
# SECTION 2: Date Range for Historical Data
# ------------------------------------------------------------
# We download price data between START_DATE and END_DATE.
# Format must be "YYYY-MM-DD" (year-month-day).
#
# WHY 5 YEARS? Long enough to capture a full market cycle
# including the COVID crash (2020) and 2022 bear market,
# but short enough to stay computationally light.
# ------------------------------------------------------------

START_DATE = "2019-01-01"
END_DATE   = "2024-12-31"


# ------------------------------------------------------------
# SECTION 3: Risk-Free Rate
# ------------------------------------------------------------
# The risk-free rate is the return you could earn with ZERO
# risk — approximated by the U.S. Treasury bill yield.
#
# WHY IT MATTERS: The Sharpe Ratio measures how much EXTRA
# return an investment earns above the risk-free rate, per
# unit of risk. A Sharpe above 1.0 is generally good.
#
# 0.043 = 4.3%, the approximate 2024 average 3-month T-bill
# yield. Update this number as interest rates change.
# ------------------------------------------------------------

RISK_FREE_RATE = 0.043   # Annual rate as a decimal (not a percentage)


# ------------------------------------------------------------
# SECTION 4: Output Directories
# ------------------------------------------------------------
# Folder paths where charts and CSV files get saved.
# Python creates these automatically if they don't exist yet.
# ------------------------------------------------------------

OUTPUT_CHARTS_DIR = "outputs/charts"
OUTPUT_DATA_DIR   = "outputs/data"


# ------------------------------------------------------------
# SECTION 5: Chart Style Settings
# ------------------------------------------------------------
# Controls the visual appearance of all plots so every chart
# looks consistent. Change CHART_STYLE here and it updates
# every chart automatically — you never touch visualizer.py
# just to change colors.
#
# Available seaborn styles:
#   "darkgrid", "whitegrid", "dark", "white", "ticks"
# ------------------------------------------------------------

CHART_STYLE      = "darkgrid"
CHART_FIGURE_DPI = 150        # Resolution of saved PNG files
CHART_PALETTE    = "tab10"    # Assigns a distinct color per ticker


# ------------------------------------------------------------
# SECTION 6: Rolling Window Size
# ------------------------------------------------------------
# The rolling volatility chart calculates volatility over a
# moving window of N trading days.
#
# Common choices:
#   21 days = 1 trading month (short-term view)
#   30 days = slightly smoother (what we use)
#   63 days = 1 trading quarter (long-term view)
# ------------------------------------------------------------

ROLLING_WINDOW = 30   # Number of trading days for rolling volatility