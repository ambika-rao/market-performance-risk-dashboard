# ============================================================
# src/data_fetcher.py
# Market Performance & Risk Analysis Dashboard
# ============================================================
# PURPOSE: This file has one job — download historical stock
# price data from Yahoo Finance and return it in a clean
# format that the rest of the project can use.
#
# WHY SEPARATE THIS? If Yahoo Finance ever changes their API,
# or you want to switch to a different data source (like
# Bloomberg or Alpha Vantage), you only change THIS file.
# Nothing else in the project needs to touch raw data.
# ============================================================

import yfinance as yf          # Downloads stock data from Yahoo Finance
import pandas as pd            # For working with tables of data
from datetime import datetime  # For validating date inputs
import sys                     # For exiting gracefully on critical errors
import warnings                # For suppressing noisy library warnings

warnings.filterwarnings("ignore", category=FutureWarning) # For suppressing noisy library warnings

def validate_dates(start_date, end_date):
    """
    Checks that the date strings are valid and in the right order.

    WHY THIS MATTERS: If you pass in a typo like "2019-13-01"
    (month 13 doesn't exist), yfinance will silently return empty
    data instead of crashing with a clear error. We catch that
    here with a helpful message instead.

    Args:
        start_date (str): Start date in "YYYY-MM-DD" format
        end_date   (str): End date in "YYYY-MM-DD" format

    Returns:
        True if dates are valid, exits the program if not
    """
    try:
        # Try to parse the date strings into real date objects
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end   = datetime.strptime(end_date,   "%Y-%m-%d")
    except ValueError:
        print(f"ERROR: Date format is wrong. Use YYYY-MM-DD format.")
        print(f"       You provided: start='{start_date}', end='{end_date}'")
        sys.exit(1)  # Exit the program with an error code

    # Make sure start comes before end
    if start >= end:
        print(f"ERROR: START_DATE must be before END_DATE.")
        print(f"       You provided: start='{start_date}', end='{end_date}'")
        sys.exit(1)

    return True


def download_price_data(tickers, start_date, end_date):
    """
    Downloads historical adjusted closing prices for a list of tickers.

    WHY ADJUSTED CLOSE? The "adjusted" closing price accounts for
    stock splits and dividends. For example, if Apple did a 4-for-1
    stock split in 2020, the raw price history would show a sudden
    drop that never actually happened. Adjusted prices fix this so
    our return calculations are accurate.

    Args:
        tickers    (list): List of ticker strings e.g. ["AAPL", "MSFT"]
        start_date (str):  Start date in "YYYY-MM-DD" format
        end_date   (str):  End date in "YYYY-MM-DD" format

    Returns:
        pandas DataFrame where each column is a ticker and each
        row is a trading day, containing the adjusted closing price
    """
    print("\n" + "="*55)
    print("  Market Performance & Risk Analysis Dashboard")
    print("="*55)
    print(f"\nDownloading data for: {', '.join(tickers)}")
    print(f"Date range: {start_date} to {end_date}\n")

    # Validate dates before attempting download
    validate_dates(start_date, end_date)

    # Download all tickers at once — yfinance handles this efficiently
    # auto_adjust=True gives us the adjusted closing prices automatically
    raw_data = yf.download(
        tickers    = tickers,
        start      = start_date,
        end        = end_date,
        auto_adjust = True,
        progress   = True    # Shows a progress bar in the terminal
    )

    # yfinance returns a multi-level column structure like:
    # (Price Type, Ticker) e.g. ("Close", "AAPL"), ("Close", "MSFT")
    # We only want the "Close" prices, one column per ticker
    prices = raw_data["Close"]

    # If only one ticker was passed, yfinance returns a Series (single column)
    # We convert it to a DataFrame to keep our code consistent
    if isinstance(prices, pd.Series):
        prices = prices.to_frame()

    # Check for tickers that returned no data (e.g. a typo in the ticker name)
    missing = [t for t in tickers if t not in prices.columns]
    if missing:
        print(f"WARNING: No data found for: {missing}")
        print(f"         Check that these tickers are valid on Yahoo Finance.")

    # Drop any columns that are entirely empty
    prices = prices.dropna(axis=1, how="all")

    # Report what we got
    valid_tickers = list(prices.columns)
    print(f"\nSuccessfully downloaded data for: {', '.join(valid_tickers) if valid_tickers else 'NONE'}")
    print(f"Trading days in dataset: {len(prices)}")

    # Only print the date range if we actually got rows back —
    # otherwise prices.index[0] would crash on an empty dataset
    if len(prices) > 0:
        print(f"Date range in data: {prices.index[0].date()} to {prices.index[-1].date()}")
    else:
        print("Date range in data: N/A (no data returned)")

    return prices

def load_or_download_prices(tickers, start_date, end_date, cache_path="outputs/data/price_cache.csv"):
    """
    Checks if we already have a saved copy of price data on disk.
    If yes, loads it instantly (no API call). If no, downloads it
    fresh and saves a copy for next time.

    WHY THIS MATTERS: Yahoo Finance enforces rate limits, and
    constantly re-downloading the same data while developing wastes
    time and risks getting temporarily blocked. Caching is standard
    practice in any data pipeline — you only hit the external API
    when you actually need fresh data.

    Args:
        tickers    (list): List of ticker strings
        start_date (str):  Start date in "YYYY-MM-DD" format
        end_date   (str):  End date in "YYYY-MM-DD" format
        cache_path (str):  Where to save/load the cached CSV

    Returns:
        pandas DataFrame of adjusted closing prices
    """
    import os

    # If a cached file already exists, load it instead of hitting the API
    if os.path.exists(cache_path):
        print(f"Found cached data at '{cache_path}' — loading from disk (no API call).")
        prices = pd.read_csv(cache_path, index_col="Date", parse_dates=True)

        # Make sure the cached file actually has the tickers we asked for
        missing_from_cache = [t for t in tickers if t not in prices.columns]
        if missing_from_cache:
            print(f"Cache is missing {missing_from_cache} — downloading fresh data instead.")
            return get_price_data(tickers, start_date, end_date)

        return prices[tickers]  # Return only the tickers requested, in order

    # No cache found — download fresh and save a copy for next time
    prices = get_price_data(tickers, start_date, end_date)

    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    prices.to_csv(cache_path)
    print(f"Saved a cached copy to '{cache_path}' for faster reruns.")

    return prices

def get_price_data(tickers, start_date, end_date):
    """
    Main entry point for this module. Downloads price data and
    performs a final check to make sure the data is usable.

    This is the function that all other modules will call —
    they never call download_price_data() directly. This extra
    layer lets us add caching or other features here later
    without changing any other file.

    Args:
        tickers    (list): List of ticker strings
        start_date (str):  Start date in "YYYY-MM-DD" format
        end_date   (str):  End date in "YYYY-MM-DD" format

    Returns:
        Clean pandas DataFrame of adjusted closing prices
    """
    prices = download_price_data(tickers, start_date, end_date)

    # Final safety check — if we got back an empty DataFrame, something
    # went wrong (bad internet connection, all tickers invalid, etc.)
    if prices.empty:
        print("\nERROR: No price data was returned. Please check:")
        print("  1. Your internet connection is working")
        print("  2. Your ticker symbols are valid (check finance.yahoo.com)")
        print("  3. Your date range contains actual trading days")
        sys.exit(1)

    # Drop any rows where ALL tickers have missing data
    # (this can happen on market holidays)
    prices = prices.dropna(how="all")

    print(f"\nData is clean and ready. Shape: {prices.shape[0]} rows x {prices.shape[1]} columns")
    print("-"*55 + "\n")

    return prices
