# ============================================================
# src/visualizer.py
# Market Performance & Risk Analysis Dashboard
# ============================================================
# PURPOSE: This file turns numbers into pictures. Each function
# takes already-calculated data (from metrics.py) and produces
# one chart, saved as a PNG file.
#
# WHY SEPARATE THIS? Plotting code looks very different from
# calculation code (lots of styling, labels, colors) and
# changes for different reasons (you might want prettier charts
# without ever touching the math). Keeping them apart follows
# the same separation-of-concerns principle as the rest of the
# project.
# ============================================================

import copy
import matplotlib.path as _mpath
import matplotlib.pyplot as plt
import seaborn as sns
import os
from matplotlib.patches import Patch    # Used for legend handles (see _add_legend)


# ------------------------------------------------------------
# Python 3.14 + matplotlib 3.10 compatibility patch
# ------------------------------------------------------------
# matplotlib's Path.__deepcopy__ calls copy.deepcopy(super(), memo),
# which triggers infinite recursion in Python 3.14 due to a change
# in how copy.deepcopy handles super() proxy objects. This affects
# legend creation, tick rendering, and savefig — essentially all
# drawing operations. We replace __deepcopy__ with a safe version
# that copies instance attributes directly without touching super().
# ------------------------------------------------------------
def _safe_path_deepcopy(self, memo):
    cls = type(self)
    result = object.__new__(cls)
    memo[id(self)] = result
    for k, v in self.__dict__.items():
        object.__setattr__(result, k, copy.deepcopy(v, memo))
    return result

_mpath.Path.__deepcopy__ = _safe_path_deepcopy


def setup_chart_style(style, palette):
    # Avoid all seaborn styles — they trigger a deepcopy recursion
    # bug in matplotlib on Python 3.14. Use rcParams directly instead.
    plt.rcParams.update({
        "axes.facecolor":    "#eaeaf2",
        "axes.edgecolor":    "white",
        "axes.grid":         True,
        "grid.color":        "white",
        "grid.linewidth":    1.0,
        "figure.facecolor":  "white",
        "font.size":         11,
        "axes.titlesize":    14,
        "axes.titleweight":  "bold",
    })
    sns.set_palette(palette)


def _add_legend(ax, labels, title="Ticker", loc="upper left", alpha=1.0):
    """
    Adds a legend using Patch proxy handles instead of the actual plot handles.

    WHY: Python 3.14 + matplotlib 3.10 have a deepcopy recursion bug that
    crashes when ax.legend() tries to copy Line2D marker internals. Using
    Patch objects bypasses that code path entirely — Patch handles don't
    carry marker state so they never trigger the deepcopy.
    """
    colors = sns.color_palette(n_colors=len(labels))
    handles = [Patch(facecolor=c, alpha=alpha, label=l)
               for c, l in zip(colors, labels)]
    ax.legend(handles=handles, title=title, loc=loc)


def save_figure(fig, filename, output_dir, dpi):
    """
    Saves a matplotlib figure to disk and closes it to free memory.

    WHY A SEPARATE FUNCTION FOR THIS? Every single plotting function
    below needs to do this exact same thing (create folder if needed,
    save at the right resolution, close the figure). Instead of
    repeating those 4 lines five times, we write it once and reuse it.
    This is the "Don't Repeat Yourself" (DRY) principle.

    Args:
        fig        (Figure): The matplotlib figure object to save
        filename   (str):    e.g. "price_history.png"
        output_dir (str):    Folder to save into, e.g. "outputs/charts"
        dpi        (int):    Resolution of the saved image
    """
    # Create the output folder if it doesn't already exist
    os.makedirs(output_dir, exist_ok=True)

    filepath = os.path.join(output_dir, filename)
    fig.savefig(filepath, dpi=dpi, bbox_inches="tight")
    plt.close(fig)  # Free up memory — important when generating many charts

    print(f"Saved chart: {filepath}")


def plot_price_history(prices, output_dir, dpi):
    """
    CHART 1: Plots the raw adjusted closing price of each ticker
    over time, on one shared chart.

    WHY THIS MATTERS: This is the most intuitive chart for anyone
    looking at the dashboard — it shows the literal price journey
    of each stock. However, it has a key LIMITATION worth noting:
    stocks with very different price levels (e.g. NVDA at $3 vs
    SPY at $220) are hard to compare visually on the same axis.
    That's exactly why we also build the cumulative return chart
    next, which fixes this by putting everything on the same
    starting point ($1).

    Args:
        prices     (DataFrame): Adjusted closing prices, columns = tickers
        output_dir (str):       Where to save the chart
        dpi        (int):       Image resolution
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot one line per ticker — prices.plot() handles this automatically
    # since each column in the DataFrame is a different ticker
    for ticker in prices.columns:
        ax.plot(prices.index, prices[ticker], label=ticker, linewidth=1.5)

    ax.set_title("Stock Price History (Adjusted Close)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price ($)")
    _add_legend(ax, list(prices.columns))

    save_figure(fig, "price_history.png", output_dir, dpi)


def plot_cumulative_returns(cumulative_returns, output_dir, dpi):
    """
    CHART 2: Plots the growth of $1 invested in each ticker over
    time — the classic "horse race" comparison chart.

    WHY THIS MATTERS: Unlike raw price, this chart puts every
    ticker on the SAME starting point (0% / $1), making it the
    fairest possible visual comparison of investment performance.
    This is the single most common chart type in fund marketing
    materials and investment research reports, because it directly
    answers: "Which investment would have made me the most money?"

    Args:
        cumulative_returns (DataFrame): Output of calculate_cumulative_returns()
        output_dir         (str):       Where to save the chart
        dpi                (int):       Image resolution
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    for ticker in cumulative_returns.columns:
        # Multiply by 100 to display as a percentage instead of a decimal
        ax.plot(
            cumulative_returns.index,
            cumulative_returns[ticker] * 100,
            label=ticker,
            linewidth=1.5,
        )

    ax.set_title("Cumulative Return Comparison")
    ax.set_xlabel("Date")
    ax.set_ylabel("Cumulative Return (%)")
    _add_legend(ax, list(cumulative_returns.columns))

    # A horizontal line at 0% makes it easy to see at a glance
    # which tickers are above vs below their starting value
    ax.axhline(y=0, color="gray", linestyle="--", linewidth=0.8)

    save_figure(fig, "cumulative_returns.png", output_dir, dpi)


def plot_return_distribution(daily_returns, output_dir, dpi):
    """
    CHART 3: Plots a histogram of daily returns for each ticker,
    showing the SHAPE of risk rather than a single risk number.

    WHY THIS MATTERS: Annualized volatility gives you one number,
    but it hides important details. Two stocks can have the same
    volatility number while looking completely different in
    practice — one might have lots of small daily moves, the other
    might have rare-but-extreme crashes. A return distribution
    reveals this shape, including a concept called "fat tails"
    (more extreme outlier days than a normal bell curve would
    predict) — something every quant and risk analyst checks for.

    Args:
        daily_returns (DataFrame): Output of calculate_daily_returns()
        output_dir    (str):       Where to save the chart
        dpi           (int):       Image resolution
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    for ticker in daily_returns.columns:
        # kde=True overlays a smoothed density curve on top of the
        # histogram bars, making the distribution shape easier to read
        sns.histplot(
            daily_returns[ticker] * 100,
            label=ticker,
            kde=False,
            alpha=0.4,
            ax=ax,
            bins=80,
            stat="density",  # Normalizes bar heights so different tickers are comparable
        )

    ax.set_title("Daily Return Distribution")
    ax.set_xlabel("Daily Return (%)")
    ax.set_ylabel("Frequency")
    _add_legend(ax, list(daily_returns.columns), alpha=0.4)

    # A vertical line at 0% separates up-days from down-days visually
    ax.axvline(x=0, color="gray", linestyle="--", linewidth=0.8)

    save_figure(fig, "return_distribution.png", output_dir, dpi)


def plot_rolling_volatility(rolling_volatility, window, output_dir, dpi):
    """
    CHART 4: Plots how each ticker's annualized volatility changed
    over time, using a moving window.

    WHY THIS MATTERS: Risk isn't constant — it has "regimes." This
    chart typically reveals dramatic, visible spikes during known
    market stress events (e.g. March 2020 COVID crash, 2022 rate
    hikes). Seeing WHEN risk spiked, not just THAT it spiked, is
    valuable for understanding what kind of market conditions make
    a given stock more dangerous to hold.

    Args:
        rolling_volatility (DataFrame): Output of calculate_rolling_volatility()
        window             (int):       The rolling window size used (for the title)
        output_dir         (str):       Where to save the chart
        dpi                (int):       Image resolution
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    for ticker in rolling_volatility.columns:
        # Multiply by 100 to display as a percentage
        ax.plot(
            rolling_volatility.index,
            rolling_volatility[ticker] * 100,
            label=ticker,
            linewidth=1.5,
        )

    ax.set_title(f"Rolling {window}-Day Annualized Volatility")
    ax.set_xlabel("Date")
    ax.set_ylabel("Annualized Volatility (%)")
    _add_legend(ax, list(rolling_volatility.columns))

    save_figure(fig, "rolling_volatility.png", output_dir, dpi)


def generate_all_charts(prices, metrics_results, config):
    """
    Master function that generates all four required charts in
    one call. Mirrors the same design pattern as calculate_all_metrics()
    in metrics.py — one clean entry point that hides the details.

    Args:
        prices          (DataFrame): Adjusted closing prices
        metrics_results (dict):      Output of calculate_all_metrics()
        config          (module):    The config.py module, for style settings

    Returns:
        None (charts are saved directly to disk)
    """
    print("Generating charts...")

    # Apply consistent styling to all charts before drawing any of them
    setup_chart_style(config.CHART_STYLE, config.CHART_PALETTE)

    plot_price_history(prices, config.OUTPUT_CHARTS_DIR, config.CHART_FIGURE_DPI)

    plot_cumulative_returns(
        metrics_results["cumulative_returns"],
        config.OUTPUT_CHARTS_DIR,
        config.CHART_FIGURE_DPI,
    )

    plot_return_distribution(
        metrics_results["daily_returns"],
        config.OUTPUT_CHARTS_DIR,
        config.CHART_FIGURE_DPI,
    )

    plot_rolling_volatility(
        metrics_results["rolling_volatility"],
        config.ROLLING_WINDOW,
        config.OUTPUT_CHARTS_DIR,
        config.CHART_FIGURE_DPI,
    )

    print("All charts generated successfully.\n")