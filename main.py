# ============================================================
# main.py
# Market Performance & Risk Analysis Dashboard
# ============================================================
# PURPOSE: This is the ONLY file you need to run. It acts as
# the "conductor" — it calls every other module in the correct
# order but does no math or plotting itself.
#
# HOW TO RUN:
#   python main.py
#
# HOW TO CUSTOMIZE:
#   Open config.py and change TICKERS, START_DATE, END_DATE,
#   or RISK_FREE_RATE. Then re-run this file. Nothing else
#   needs to change.
#
# OUTPUT:
#   outputs/charts/  — four PNG chart files
#   outputs/data/    — summary_metrics.csv, daily_returns.csv
# ============================================================

import time                        # For measuring how long the run takes

import config                      # All project settings live here

from src.data_fetcher import load_or_download_prices   # Downloads + caches price data
from src.metrics     import calculate_all_metrics      # Six financial calculations
from src.visualizer  import generate_all_charts        # Four chart PNG files
from src.reporter    import generate_report            # Summary table + CSV export


def main():
    """
    Runs the full dashboard pipeline from data download to saved outputs.

    The five steps below mirror the logical flow of any quantitative
    analysis pipeline you'll encounter in a finance role:
        1. Acquire data
        2. Calculate metrics
        3. Visualize results
        4. Report findings
    """
    run_start = time.time()   # Start the clock so we can report total runtime

    # ----------------------------------------------------------
    # STEP 1: Load Price Data
    # ----------------------------------------------------------
    # load_or_download_prices() checks for a cached CSV first.
    # If found, it loads instantly. If not, it downloads from
    # Yahoo Finance and saves a copy for next time.
    # All settings (tickers, dates) come from config.py.
    # ----------------------------------------------------------
    prices = load_or_download_prices(
        tickers    = config.TICKERS,
        start_date = config.START_DATE,
        end_date   = config.END_DATE,
    )

    # ----------------------------------------------------------
    # STEP 2: Calculate All Financial Metrics
    # ----------------------------------------------------------
    # One function call — it returns a dictionary containing:
    #   daily_returns, cumulative_returns, annualized_return,
    #   annualized_volatility, sharpe_ratio, max_drawdown,
    #   rolling_volatility
    # ----------------------------------------------------------
    metrics_results = calculate_all_metrics(
        prices         = prices,
        risk_free_rate = config.RISK_FREE_RATE,
        rolling_window = config.ROLLING_WINDOW,
    )

    # ----------------------------------------------------------
    # STEP 3: Generate All Charts
    # ----------------------------------------------------------
    # Saves four PNG files to outputs/charts/:
    #   price_history.png, cumulative_returns.png,
    #   return_distribution.png, rolling_volatility.png
    # ----------------------------------------------------------
    generate_all_charts(
        prices          = prices,
        metrics_results = metrics_results,
        config          = config,
    )

    # ----------------------------------------------------------
    # STEP 4: Generate Report
    # ----------------------------------------------------------
    # Prints the summary table to the terminal and saves two
    # CSV files to outputs/data/:
    #   summary_metrics.csv, daily_returns.csv
    # ----------------------------------------------------------
    generate_report(
        metrics_results = metrics_results,
        config          = config,
    )

    # ----------------------------------------------------------
    # Done — print total elapsed time
    # ----------------------------------------------------------
    elapsed = time.time() - run_start
    print(f"Dashboard complete in {elapsed:.1f}s.")
    print(f"Charts saved to  : {config.OUTPUT_CHARTS_DIR}/")
    print(f"Data saved to    : {config.OUTPUT_DATA_DIR}/")


# ============================================================
# Entry point guard
# ============================================================
# This block ensures main() only runs when you execute this
# file directly ("python main.py"). If another file ever
# imports main.py, it won't accidentally trigger the full
# pipeline — a standard Python best practice.
# ============================================================
if __name__ == "__main__":
    main()
