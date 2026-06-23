# ============================================================
# src/metrics.py
# Market Performance & Risk Analysis Dashboard
# ============================================================
# PURPOSE: This file calculates every financial metric the
# dashboard reports. Each function takes price data in and
# returns a calculated result out — no downloading, no
# plotting, no printing happens here. Just math.
#
# WHY SEPARATE THIS? This is the most reusable, most testable
# part of the whole project. By keeping it pure (no side
# effects), we can write unit tests for it later, and reuse
# it in a totally different project (a trading bot, a web
# app, etc.) without changing a single line.
# ============================================================

import pandas as pd
import numpy as np


# ------------------------------------------------------------
# TRADING_DAYS_PER_YEAR
# ------------------------------------------------------------
# The US stock market is open roughly 252 days a year (365 days
# minus weekends and ~9 public holidays). This constant is used
# to "annualize" daily statistics — i.e. scale a daily number
# up to what it would look like over a full year.
# ------------------------------------------------------------
TRADING_DAYS_PER_YEAR = 252


def calculate_daily_returns(prices):
    """
    Calculates the percentage change in price from one trading
    day to the next, for every ticker.

    WHY THIS MATTERS: Daily return is the most fundamental unit
    of measurement in finance. A stock going from $100 to $102
    has a daily return of 2% — this tells us the percentage
    gain/loss, which is far more useful for comparison than the
    raw dollar change (a $2 move means something very different
    for a $10 stock vs a $1,000 stock).

    Formula: (Price_today - Price_yesterday) / Price_yesterday

    Args:
        prices (DataFrame): Adjusted closing prices, columns = tickers

    Returns:
        DataFrame of daily returns (same shape, first row will be NaN
        since there's no "previous day" to compare the first day to)
    """
    # .pct_change() does exactly the formula above, automatically,
    # for every column (ticker) at once
    daily_returns = prices.pct_change()

    # Drop the first row — it's always NaN because there's no
    # previous day to calculate a return against
    daily_returns = daily_returns.dropna(how="all")

    return daily_returns


def calculate_cumulative_returns(daily_returns):
    """
    Calculates how much $1 invested at the start would have grown
    to, at every point in time, for each ticker.

    WHY THIS MATTERS: This is the metric behind every "growth of
    $10,000" chart you see in fund fact sheets. It answers the
    question an investor actually cares about: "If I had put money
    in on day 1, what would it be worth today?"

    Formula: cumulative_return_t = (1 + r_1) * (1 + r_2) * ... * (1 + r_t) - 1

    This is NOT the same as just adding up daily returns — because
    returns compound. A +10% day followed by a -10% day does NOT
    bring you back to even (it leaves you at -1%), and this formula
    correctly captures that compounding effect.

    Args:
        daily_returns (DataFrame): Output of calculate_daily_returns()

    Returns:
        DataFrame of cumulative returns, where 0.0 = no change,
        0.50 = up 50%, -0.20 = down 20%, etc.
    """
    # (1 + daily_returns) gives us the daily "growth factor"
    # e.g. a 2% return becomes 1.02, a -3% return becomes 0.97
    growth_factors = 1 + daily_returns

    # .cumprod() multiplies all growth factors together as we move
    # through time — this is what "compounding" means mathematically
    cumulative_growth = growth_factors.cumprod()

    # Subtract 1 to convert back from a growth factor to a percentage
    # change (e.g. 1.50 growth factor = +50% cumulative return)
    cumulative_returns = cumulative_growth - 1

    return cumulative_returns


def calculate_annualized_return(daily_returns):
    """
    Converts the average daily return into an equivalent yearly
    growth rate.

    WHY THIS MATTERS: You can't fairly compare "this stock returned
    8% over 3 years" vs "this stock returned 5% over 6 months" without
    putting them on the same time scale. Annualizing solves this by
    asking: "if this average daily performance continued for a full
    year, what would the yearly return be?"

    Formula: (1 + mean_daily_return) ^ 252 - 1

    We use 252 (trading days per year) as the exponent because
    returns COMPOUND daily, not just add up.

    Args:
        daily_returns (DataFrame): Output of calculate_daily_returns()

    Returns:
        Series with one annualized return value per ticker
    """
    mean_daily_return = daily_returns.mean()

    # Compound the average daily return over a full trading year
    annualized_return = (1 + mean_daily_return) ** TRADING_DAYS_PER_YEAR - 1

    return annualized_return


def calculate_annualized_volatility(daily_returns):
    """
    Measures how much a stock's daily returns swing around their
    average, scaled up to a yearly figure. This is the standard
    definition of "risk" in modern finance.

    WHY THIS MATTERS: Two stocks can have the same average return
    but very different RISK profiles. Imagine Stock A moves +1%/-1%
    every day, while Stock B swings +10%/-10% — they might average
    the same return, but Stock B is far riskier. Volatility captures
    that swinginess using standard deviation (a statistics concept
    you already know from your actuarial coursework).

    Formula: daily_std_dev * sqrt(252)

    WHY MULTIPLY BY THE SQUARE ROOT OF 252 (not just 252)?
    Variance scales linearly with time, but standard deviation is
    the SQUARE ROOT of variance. So when we scale daily variance up
    to yearly variance (x252), we must take the square root of that
    scaling factor to correctly scale the standard deviation. This
    is a classic result from statistics: std dev scales with sqrt(time).

    Args:
        daily_returns (DataFrame): Output of calculate_daily_returns()

    Returns:
        Series with one annualized volatility value per ticker
        (expressed as a decimal, e.g. 0.25 = 25% annual volatility)
    """
    daily_std_dev = daily_returns.std()

    # Scale daily standard deviation up to an annual figure
    annualized_volatility = daily_std_dev * np.sqrt(TRADING_DAYS_PER_YEAR)

    return annualized_volatility


def calculate_sharpe_ratio(annualized_return, annualized_volatility, risk_free_rate):
    """
    Calculates risk-adjusted return: how much extra return an
    investment earns above the "safe" risk-free rate, per unit
    of risk (volatility) taken on.

    WHY THIS MATTERS: This is arguably THE most important metric
    in portfolio management, created by Nobel laureate William
    Sharpe. A stock returning 20% sounds great — but if it took on
    enormous risk to get there, that might be a worse investment
    than a stock returning 10% with very little risk. The Sharpe
    Ratio lets you compare investments on a level playing field by
    answering: "How much return am I getting paid for the risk I'm
    taking?"

    Formula: (annualized_return - risk_free_rate) / annualized_volatility

    Rule of thumb interpretation:
        Sharpe < 0    : Losing money relative to a risk-free investment
        Sharpe 0 - 1  : Sub-optimal risk-adjusted return
        Sharpe 1 - 2  : Good
        Sharpe 2 - 3  : Very good
        Sharpe > 3    : Excellent (rare over long periods)

    Args:
        annualized_return     (Series): Output of calculate_annualized_return()
        annualized_volatility (Series): Output of calculate_annualized_volatility()
        risk_free_rate         (float): The "safe" baseline rate, e.g. 0.043 for 4.3%

    Returns:
        Series with one Sharpe ratio value per ticker
    """
    # The numerator is called "excess return" — the return earned
    # ABOVE what you'd get from a risk-free investment like T-bills
    excess_return = annualized_return - risk_free_rate

    sharpe_ratio = excess_return / annualized_volatility

    return sharpe_ratio


def calculate_max_drawdown(cumulative_returns):
    """
    Finds the single worst percentage decline from a peak to a
    subsequent trough, for each ticker, over the entire period.

    WHY THIS MATTERS: Average returns and volatility don't tell you
    about the WORST psychological pain an investor experienced.
    Max drawdown answers a very human question: "At the worst possible
    moment, how much of my money had I lost from its highest point?"
    This matters enormously for behavioral reasons — large drawdowns
    are what cause investors to panic-sell at the bottom.

    Formula:
        running_max = the highest cumulative value seen so far, at each point in time
        drawdown_t  = (cumulative_value_t - running_max_t) / running_max_t
        max_drawdown = the minimum (most negative) value of drawdown_t

    Args:
        cumulative_returns (DataFrame): Output of calculate_cumulative_returns()

    Returns:
        Series with one max drawdown value per ticker
        (always negative or zero, e.g. -0.35 = a 35% peak-to-trough decline)
    """
    # Convert cumulative returns into a "wealth index" — i.e. what
    # $1 invested at the start would be worth at each point in time.
    # We add 1 because cumulative_returns are stored as 0.0 = no change.
    wealth_index = 1 + cumulative_returns

    # .cummax() tracks the running historical peak at each point in time
    running_max = wealth_index.cummax()

    # Drawdown = how far below that peak we currently are, as a percentage
    drawdown = (wealth_index - running_max) / running_max

    # The max drawdown is the single worst (most negative) point reached
    max_drawdown = drawdown.min()

    return max_drawdown


def calculate_rolling_volatility(daily_returns, window):
    """
    Calculates annualized volatility over a moving window of N days,
    instead of using the entire history at once. This shows how
    risk changes over TIME rather than giving one static number.

    WHY THIS MATTERS: A stock's riskiness isn't constant — it can be
    calm for years and then suddenly turn volatile (think: COVID
    crash in March 2020). A single volatility number for the whole
    5-year period would hide this. Rolling volatility reveals when
    risk spiked, which is critical for understanding market regimes.

    Args:
        daily_returns (DataFrame): Output of calculate_daily_returns()
        window           (int):    Number of trading days in the
                                    rolling window (e.g. 30)

    Returns:
        DataFrame of rolling annualized volatility, same shape as
        input (the first `window` rows will be NaN since there
        aren't enough days yet to calculate a full window)
    """
    # .rolling(window) creates a moving N-day lookback at each point,
    # then .std() calculates the standard deviation within that window
    rolling_std = daily_returns.rolling(window=window).std()

    # Annualize it the same way we did for the whole-period volatility
    rolling_volatility = rolling_std * np.sqrt(TRADING_DAYS_PER_YEAR)

    return rolling_volatility


def calculate_all_metrics(prices, risk_free_rate, rolling_window):
    """
    Master function that runs every calculation in the correct
    order and returns everything in one organized dictionary.

    WHY THIS MATTERS (DESIGN PATTERN): This function is the ONLY
    one that other files (like main.py) need to call. It hides
    the internal order-of-operations (e.g. you must calculate
    daily returns BEFORE cumulative returns) behind one clean
    interface. This is called encapsulation — a core software
    engineering principle.

    Args:
        prices         (DataFrame): Adjusted closing prices
        risk_free_rate (float):     e.g. 0.043 for 4.3%
        rolling_window (int):       e.g. 30 for a 30-day window

    Returns:
        dict containing every calculated metric, keyed by name
    """
    print("Calculating financial metrics...")

    # Step 1: Daily returns are the foundation everything else builds on
    daily_returns = calculate_daily_returns(prices)

    # Step 2: Cumulative returns build on daily returns
    cumulative_returns = calculate_cumulative_returns(daily_returns)

    # Step 3: Annualized return and volatility both build on daily returns
    annualized_return = calculate_annualized_return(daily_returns)
    annualized_volatility = calculate_annualized_volatility(daily_returns)

    # Step 4: Sharpe ratio builds on annualized return AND volatility
    sharpe_ratio = calculate_sharpe_ratio(
        annualized_return, annualized_volatility, risk_free_rate
    )

    # Step 5: Max drawdown builds on cumulative returns
    max_drawdown = calculate_max_drawdown(cumulative_returns)

    # Step 6: Rolling volatility builds on daily returns
    rolling_volatility = calculate_rolling_volatility(daily_returns, rolling_window)

    print("Metrics calculated successfully.\n")

    # Package everything into one dictionary for easy access elsewhere
    return {
        "daily_returns": daily_returns,
        "cumulative_returns": cumulative_returns,
        "annualized_return": annualized_return,
        "annualized_volatility": annualized_volatility,
        "sharpe_ratio": sharpe_ratio,
        "max_drawdown": max_drawdown,
        "rolling_volatility": rolling_volatility,
    }