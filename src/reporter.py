# ============================================================
# src/reporter.py
# Market Performance & Risk Analysis Dashboard
# ============================================================
# PURPOSE: This file has two jobs:
#   1. Build a human-readable summary table ranking every ticker
#      across all six financial metrics, and print it to the
#      terminal using tabulate.
#   2. Save two CSV files to disk:
#        - summary_metrics.csv  : the ranking table
#        - daily_returns.csv    : full daily return time series
#
# WHY SEPARATE THIS? Formatting output for humans (percentages,
# rounding, alignment) is completely different work from doing
# math (metrics.py) or drawing charts (visualizer.py). Keeping
# it separate means you can change how results are displayed
# without ever touching the calculation logic.
# ============================================================

import os
import pandas as pd
from tabulate import tabulate   # Formats tables for clean terminal output


# ============================================================
# SECTION 1: Build the Summary Table
# ============================================================

def build_summary_table(metrics_results):
    """
    Assembles one row per ticker containing all six key metrics,
    formatted as human-readable percentages and rounded decimals.

    WHY THIS TABLE MATTERS: This is what a portfolio manager or
    interviewer sees first. Instead of hunting through four separate
    charts to compare two stocks, this table puts every metric
    side by side — making it immediately clear which stock has
    the best risk-adjusted return, which is the most volatile, etc.

    Columns produced:
        Ticker               — stock symbol
        Ann. Return (%)      — annualized return as a percentage
        Ann. Volatility (%)  — annualized volatility as a percentage
        Sharpe Ratio         — unitless risk-adjusted return score
        Max Drawdown (%)     — worst peak-to-trough decline as a percentage
        Total Cum. Return (%)— total percentage gain/loss over the full period

    Args:
        metrics_results (dict): Output of calculate_all_metrics() from metrics.py

    Returns:
        pandas DataFrame with one row per ticker, sorted by Sharpe Ratio
        descending (best risk-adjusted return first)
    """

    # Pull out the individual metric Series from the results dictionary.
    # Each of these is a pandas Series with ticker symbols as the index.
    ann_return     = metrics_results["annualized_return"]
    ann_volatility = metrics_results["annualized_volatility"]
    sharpe         = metrics_results["sharpe_ratio"]
    max_dd         = metrics_results["max_drawdown"]
    cum_returns    = metrics_results["cumulative_returns"]

    # The cumulative_returns DataFrame has one row per trading day.
    # We only want the FINAL value (the last row) — that's the total
    # cumulative return earned over the entire period.
    total_cum_return = cum_returns.iloc[-1]

    # Build the summary as a dictionary and then convert to DataFrame.
    # Each key becomes a column; values are Series indexed by ticker.
    summary = pd.DataFrame({
        "Ann. Return (%)":       (ann_return     * 100).round(2),
        "Ann. Volatility (%)":   (ann_volatility * 100).round(2),
        "Sharpe Ratio":          sharpe.round(3),
        "Max Drawdown (%)":      (max_dd         * 100).round(2),
        "Total Cum. Return (%)": (total_cum_return * 100).round(2),
    })

    # The index is currently the ticker symbols (e.g. "AAPL", "MSFT").
    # Move it into its own column so it appears as the first column in
    # the table and in the CSV.
    summary.index.name = "Ticker"
    summary = summary.reset_index()

    # Sort by Sharpe Ratio descending so the best risk-adjusted
    # performer appears at the top of the table — same convention
    # used in professional fund screening tools.
    summary = summary.sort_values("Sharpe Ratio", ascending=False)
    summary = summary.reset_index(drop=True)   # Clean up row numbers after sort

    return summary


def add_rank_column(summary_df):
    """
    Inserts a "Rank" column at the front of the table, numbered 1, 2, 3...
    based on the current sort order (Sharpe Ratio descending).

    This is a small UX touch: it makes the table read like a leaderboard,
    which is intuitive and looks polished in a terminal printout.

    Args:
        summary_df (DataFrame): Output of build_summary_table()

    Returns:
        DataFrame with a "Rank" column prepended
    """
    summary_df.insert(0, "Rank", range(1, len(summary_df) + 1))
    return summary_df


# ============================================================
# SECTION 2: Print the Summary Table to the Terminal
# ============================================================

def print_summary_table(summary_df):
    """
    Prints the summary table to the terminal using tabulate, which
    automatically aligns columns and draws clean ASCII borders.

    WHY TABULATE? Python's default print(dataframe) produces messy,
    inconsistent spacing. tabulate formats the table the way you'd
    see it in a professional CLI tool or financial report.

    Args:
        summary_df (DataFrame): Output of build_summary_table() or
                                add_rank_column()

    Returns:
        None (prints to terminal)
    """
    print("\n" + "=" * 70)
    print("  PERFORMANCE & RISK SUMMARY  (sorted by Sharpe Ratio, best first)")
    print("=" * 70)

    # "github" style uses pipe characters — clean and readable in any terminal
    # showindex=False because we moved the ticker into its own column already
    print(tabulate(
        summary_df,
        headers="keys",
        tablefmt="github",
        showindex=False,
        floatfmt=".2f",       # Consistent 2-decimal formatting across all floats
    ))

    print("=" * 70)

    # Print a brief interpretation guide so the output is self-explanatory
    # to anyone who runs the script without reading the docs.
    print("\nINTERPRETATION GUIDE:")
    print("  Ann. Return (%)      — Higher is better. Yearly growth rate.")
    print("  Ann. Volatility (%)  — Lower is better. Measures risk / price swings.")
    print("  Sharpe Ratio         — Higher is better. Return per unit of risk taken.")
    print("                         >1 = good, >2 = very good, >3 = excellent.")
    print("  Max Drawdown (%)     — Less negative is better. Worst peak-to-trough loss.")
    print("  Total Cum. Return (%)— Higher is better. Total gain/loss over full period.")
    print()


# ============================================================
# SECTION 3: Save Results to CSV
# ============================================================

def save_summary_csv(summary_df, output_dir):
    """
    Saves the summary metrics table to a CSV file.

    WHY SAVE AS CSV? CSV (comma-separated values) is the universal
    language of data — it opens in Excel, Google Sheets, R, or any
    other tool without any conversion. This makes your project output
    immediately useful to anyone who wants to do further analysis.

    Args:
        summary_df (DataFrame): Output of build_summary_table()
        output_dir (str):       Folder path, e.g. "outputs/data"

    Returns:
        None (file is saved to disk)
    """
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, "summary_metrics.csv")

    # index=False because the Ticker is already a regular column,
    # not the DataFrame index — so we don't need a redundant index column
    summary_df.to_csv(filepath, index=False)
    print(f"Saved summary table : {filepath}")


def save_daily_returns_csv(daily_returns, output_dir):
    """
    Saves the full daily return time series to a CSV file.

    WHY SAVE THIS? Daily returns are the raw ingredient for almost
    every other financial analysis. Saving them lets you (or a future
    user) reload them and calculate additional metrics — like Value at
    Risk, Conditional VaR, or Sortino Ratio — without re-downloading
    price data from Yahoo Finance.

    Args:
        daily_returns (DataFrame): Output of calculate_daily_returns() from metrics.py
                                   Columns = tickers, index = trading dates
        output_dir    (str):       Folder path, e.g. "outputs/data"

    Returns:
        None (file is saved to disk)
    """
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, "daily_returns.csv")

    # index=True here because the index IS meaningful — it's the trading date
    daily_returns.to_csv(filepath, index=True)
    print(f"Saved daily returns : {filepath}")


# ============================================================
# SECTION 4: Master Function (called by main.py)
# ============================================================

def generate_report(metrics_results, config):
    """
    Master function that builds the summary table, prints it, and
    saves both CSV files in one call.

    Mirrors the same design pattern as calculate_all_metrics() in
    metrics.py and generate_all_charts() in visualizer.py — every
    module exposes one clean entry point that main.py calls, hiding
    all internal steps behind a single function name.

    Args:
        metrics_results (dict):   Output of calculate_all_metrics()
        config          (module): The config.py module, for output paths

    Returns:
        summary_df (DataFrame): The summary table, in case the caller
                                wants to use it for further processing
    """
    print("Generating performance report...")

    # Step 1: Build the table with all metrics per ticker
    summary_df = build_summary_table(metrics_results)

    # Step 2: Add rank column (1 = best Sharpe Ratio)
    summary_df = add_rank_column(summary_df)

    # Step 3: Print the table to the terminal
    print_summary_table(summary_df)

    # Step 4: Save both CSV outputs
    save_summary_csv(summary_df, config.OUTPUT_DATA_DIR)
    save_daily_returns_csv(
        metrics_results["daily_returns"],
        config.OUTPUT_DATA_DIR
    )

    print("Report complete.\n")

    return summary_df
