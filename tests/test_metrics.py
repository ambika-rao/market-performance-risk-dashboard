# ============================================================
# tests/test_metrics.py
# Market Performance & Risk Analysis Dashboard
# ============================================================
# PURPOSE: Unit tests for every function in src/metrics.py.
#
# WHY UNIT TESTS MATTER IN FINANCE: A bug in a financial
# calculation is far more dangerous than a bug in a UI. If
# your Sharpe Ratio formula is off by one small error, every
# ranking and investment decision built on it is wrong — and
# you might not notice until it's too late. Tests catch that.
#
# PHILOSOPHY OF THESE TESTS: Every test case is designed so
# you can verify the expected answer with pencil and paper
# (or a calculator). If you can't compute the expected value
# by hand from the formula, the test is testing the wrong
# thing. We always check:
#   1. A known input → known output (the "happy path")
#   2. A boundary case (zero, constant, all-up, all-down)
#   3. A property that must always hold (e.g. drawdown ≤ 0)
#
# HOW TO RUN:
#   From the project root directory:
#       python -m unittest discover -s tests -v
#
#   Or run just this file:
#       python -m unittest tests.test_metrics -v
# ============================================================

import unittest
import sys
import os
import numpy as np
import pandas as pd

# Add the project root to Python's search path so that
# "from src.metrics import ..." works regardless of where
# the test runner is invoked from.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.metrics import (
    calculate_daily_returns,
    calculate_cumulative_returns,
    calculate_annualized_return,
    calculate_annualized_volatility,
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    calculate_rolling_volatility,
    calculate_all_metrics,
    TRADING_DAYS_PER_YEAR,
)


# ============================================================
# Helper: build a simple price DataFrame for reuse
# ============================================================
def _prices(values, ticker="TEST"):
    """Returns a one-column DataFrame with a numeric index."""
    return pd.DataFrame({ticker: values}, dtype=float)


def _returns(values, ticker="TEST"):
    """Returns a one-column DataFrame of pre-built daily returns."""
    return pd.DataFrame({ticker: values}, dtype=float)


# ============================================================
# 1. Daily Returns
# ============================================================
class TestCalculateDailyReturns(unittest.TestCase):
    """
    Formula tested: r_t = (P_t - P_{t-1}) / P_{t-1}

    This is the most fundamental formula in quantitative finance.
    Every other metric in this project builds on daily returns,
    so getting this right is critical.
    """

    def test_known_two_period_series(self):
        # $100 → $110: return = (110 - 100) / 100 = +10%
        # $110 → $99:  return = (99 - 110) / 110 ≈ -10%
        prices = _prices([100.0, 110.0, 99.0])
        returns = calculate_daily_returns(prices)
        self.assertAlmostEqual(returns["TEST"].iloc[0],  0.10, places=10)
        self.assertAlmostEqual(returns["TEST"].iloc[1], -0.10, places=10)

    def test_row_count_is_one_less_than_prices(self):
        # 3 price observations → 2 return observations.
        # The first row is always dropped (no "previous day" on day 0).
        prices = _prices([100.0, 110.0, 99.0])
        returns = calculate_daily_returns(prices)
        self.assertEqual(len(returns), 2)

    def test_flat_price_series_gives_zero_returns(self):
        # A stock that never moves has 0% daily returns every day.
        prices = _prices([50.0, 50.0, 50.0, 50.0])
        returns = calculate_daily_returns(prices)
        self.assertTrue((returns["TEST"] == 0.0).all())

    def test_multiple_tickers_calculated_independently(self):
        prices = pd.DataFrame({"A": [100.0, 120.0], "B": [200.0, 180.0]})
        returns = calculate_daily_returns(prices)
        self.assertAlmostEqual(returns["A"].iloc[0],  0.20, places=10)  # +20%
        self.assertAlmostEqual(returns["B"].iloc[0], -0.10, places=10)  # -10%


# ============================================================
# 2. Cumulative Returns
# ============================================================
class TestCalculateCumulativeReturns(unittest.TestCase):
    """
    Formula tested: C_t = (1+r_1)(1+r_2)...(1+r_t) - 1

    KEY FINANCE INSIGHT: A +10% gain followed by a -10% loss
    does NOT bring you back to even — it leaves you at -1%.
    This is why compounding is non-intuitive and why the
    formula uses multiplication, not addition.

    Proof: (1.10)(0.90) = 0.99 → cumulative return = -1%
    This is also why a 50% loss requires a 100% gain to recover.
    """

    def test_compounding_is_not_additive(self):
        # +10% then -10%: most people guess 0%, the real answer is -1%
        # (1.10)(0.90) - 1 = 0.99 - 1 = -0.01
        daily = _returns([0.10, -0.10])
        cum = calculate_cumulative_returns(daily)
        self.assertAlmostEqual(cum["TEST"].iloc[-1], -0.01, places=10)

    def test_first_period_equals_first_return(self):
        # After just one period, cumulative return = that period's return
        # C_1 = (1 + r_1) - 1 = r_1
        daily = _returns([0.05, 0.03, -0.02])
        cum = calculate_cumulative_returns(daily)
        self.assertAlmostEqual(cum["TEST"].iloc[0], 0.05, places=10)

    def test_three_periods_of_constant_growth(self):
        # 1% every day for 3 days: (1.01)^3 - 1 = 1.030301 - 1 = 0.030301
        daily = _returns([0.01, 0.01, 0.01])
        cum = calculate_cumulative_returns(daily)
        expected = (1.01 ** 3) - 1
        self.assertAlmostEqual(cum["TEST"].iloc[-1], expected, places=10)

    def test_all_negative_returns_stay_negative(self):
        # Losing money every day → cumulative return always negative
        daily = _returns([-0.01, -0.01, -0.01])
        cum = calculate_cumulative_returns(daily)
        self.assertTrue((cum["TEST"] < 0).all())


# ============================================================
# 3. Annualized Return
# ============================================================
class TestCalculateAnnualizedReturn(unittest.TestCase):
    """
    Formula tested: (1 + mean_daily_return)^252 - 1

    WHY 252? The US market trades ~252 days per year.
    WHY AN EXPONENT? Returns compound. Adding up 252 daily
    returns gives arithmetic return — wrong. The geometric
    formula (exponent) correctly captures compounding, which
    is what actually happens to your money.
    """

    def test_zero_daily_returns_annualize_to_zero(self):
        # 0% every day → 0% for the year. Trivial but verifies the formula.
        daily = _returns([0.0] * 252)
        ann = calculate_annualized_return(daily)
        self.assertAlmostEqual(ann["TEST"], 0.0, places=10)

    def test_known_constant_daily_return(self):
        # A constant daily return of 0.1% annualizes to (1.001)^252 - 1
        daily_r = 0.001
        daily = _returns([daily_r] * 252)
        ann = calculate_annualized_return(daily)
        expected = (1 + daily_r) ** TRADING_DAYS_PER_YEAR - 1
        self.assertAlmostEqual(ann["TEST"], expected, places=10)

    def test_negative_average_return_annualizes_negative(self):
        # Losing a little each day → negative annualized return
        daily = _returns([-0.001] * 100)
        ann = calculate_annualized_return(daily)
        self.assertLess(ann["TEST"], 0.0)

    def test_annualized_return_is_higher_than_simple_sum(self):
        # For positive returns, compounding (geometric) always exceeds
        # the simple arithmetic sum — this is how compounding "works for you"
        daily_r = 0.001
        daily = _returns([daily_r] * 252)
        ann = calculate_annualized_return(daily)
        arithmetic_sum = daily_r * 252
        self.assertGreater(ann["TEST"], arithmetic_sum)


# ============================================================
# 4. Annualized Volatility
# ============================================================
class TestCalculateAnnualizedVolatility(unittest.TestCase):
    """
    Formula tested: std(daily_returns) * sqrt(252)

    WHY sqrt(252)? Variance scales linearly with time, but
    standard deviation is the square root of variance — so
    std scales with sqrt(time). This is the same square-root-
    of-time rule used in actuarial risk models.

    This is "the" formula for annualizing any daily risk measure.
    """

    def test_constant_returns_give_zero_volatility(self):
        # If returns never vary, std dev = 0 → volatility = 0.
        # A stock with zero volatility would be like a savings account.
        daily = _returns([0.01] * 100)
        vol = calculate_annualized_volatility(daily)
        self.assertAlmostEqual(vol["TEST"], 0.0, places=10)

    def test_known_standard_deviation(self):
        # Build a series where we control the std exactly.
        # numpy std with ddof=1 should match pandas .std().
        np.random.seed(42)
        raw = np.random.normal(0, 0.01, 500)    # daily std = ~0.01
        daily = _returns(raw)
        vol = calculate_annualized_volatility(daily)
        expected = np.std(raw, ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR)
        self.assertAlmostEqual(vol["TEST"], expected, places=10)

    def test_volatility_is_always_non_negative(self):
        # Standard deviation is always ≥ 0 by definition.
        daily = _returns([-0.05, 0.03, -0.02, 0.04, -0.01])
        vol = calculate_annualized_volatility(daily)
        self.assertGreaterEqual(vol["TEST"], 0.0)

    def test_higher_swing_gives_higher_volatility(self):
        # A stock that swings ±5% daily is riskier than one swinging ±1%
        low_vol  = _returns([ 0.01, -0.01,  0.01, -0.01] * 25)
        high_vol = _returns([ 0.05, -0.05,  0.05, -0.05] * 25)
        v_low  = calculate_annualized_volatility(low_vol)
        v_high = calculate_annualized_volatility(high_vol)
        self.assertGreater(v_high["TEST"], v_low["TEST"])


# ============================================================
# 5. Sharpe Ratio
# ============================================================
class TestCalculateSharpeRatio(unittest.TestCase):
    """
    Formula tested: (annualized_return - risk_free_rate) / annualized_volatility

    This is arguably the most important metric in portfolio
    management (Nobel Prize, 1990). It answers: "How much
    extra return am I earning above the risk-free rate, per
    unit of risk I'm taking on?"

    Interviewers at asset managers WILL ask you to explain this.
    """

    def test_known_values(self):
        # Sharpe = (0.10 - 0.02) / 0.20 = 0.08 / 0.20 = 0.40
        # You can verify this with a $1 calculator.
        ann_r = pd.Series({"TEST": 0.10})
        ann_v = pd.Series({"TEST": 0.20})
        sharpe = calculate_sharpe_ratio(ann_r, ann_v, risk_free_rate=0.02)
        self.assertAlmostEqual(sharpe["TEST"], 0.40, places=10)

    def test_negative_sharpe_when_return_below_risk_free(self):
        # If your investment returns 3% but T-bills pay 5%, you were
        # better off in T-bills. Sharpe correctly turns negative here.
        ann_r = pd.Series({"TEST": 0.03})
        ann_v = pd.Series({"TEST": 0.20})
        sharpe = calculate_sharpe_ratio(ann_r, ann_v, risk_free_rate=0.05)
        self.assertLess(sharpe["TEST"], 0.0)

    def test_zero_risk_free_rate(self):
        # When rf = 0, Sharpe simplifies to return / volatility
        ann_r = pd.Series({"TEST": 0.12})
        ann_v = pd.Series({"TEST": 0.30})
        sharpe = calculate_sharpe_ratio(ann_r, ann_v, risk_free_rate=0.0)
        self.assertAlmostEqual(sharpe["TEST"], 0.12 / 0.30, places=10)

    def test_higher_return_same_volatility_gives_higher_sharpe(self):
        # Holding volatility constant, more return → better Sharpe.
        # This is the direction every portfolio manager tries to move.
        ann_v   = pd.Series({"TEST": 0.20})
        sharpe_low  = calculate_sharpe_ratio(pd.Series({"TEST": 0.05}), ann_v, 0.02)
        sharpe_high = calculate_sharpe_ratio(pd.Series({"TEST": 0.20}), ann_v, 0.02)
        self.assertGreater(sharpe_high["TEST"], sharpe_low["TEST"])

    def test_same_return_lower_volatility_gives_higher_sharpe(self):
        # Same return but less risk → better Sharpe.
        # This is why diversification (which reduces vol) improves Sharpe.
        ann_r    = pd.Series({"TEST": 0.12})
        sharpe_risky = calculate_sharpe_ratio(ann_r, pd.Series({"TEST": 0.40}), 0.04)
        sharpe_safe  = calculate_sharpe_ratio(ann_r, pd.Series({"TEST": 0.10}), 0.04)
        self.assertGreater(sharpe_safe["TEST"], sharpe_risky["TEST"])


# ============================================================
# 6. Maximum Drawdown
# ============================================================
class TestCalculateMaxDrawdown(unittest.TestCase):
    """
    Formula tested:
        wealth_index  = 1 + cumulative_return
        running_max_t = max(wealth_index_0, ..., wealth_index_t)
        drawdown_t    = (wealth_index_t - running_max_t) / running_max_t
        max_drawdown  = min(drawdown_t)

    EXAMPLE from the data: NVDA had a ~-66% max drawdown over
    2019-2024, meaning someone who bought at the peak in late
    2021 lost two-thirds of their investment before recovery.
    Max drawdown is what risk managers use to estimate "worst
    case pain" for investors.
    """

    def test_known_peak_to_trough(self):
        # Wealth: 1.0 → 1.1 → 1.2 → 0.9
        # Peak = 1.2 at day 2, trough = 0.9 at day 3
        # Drawdown = (0.9 - 1.2) / 1.2 = -0.25  (exactly -25%)
        cum = _returns([0.0, 0.1, 0.2, -0.10])
        dd = calculate_max_drawdown(cum)
        self.assertAlmostEqual(dd["TEST"], -0.25, places=10)

    def test_always_rising_gives_zero_drawdown(self):
        # A stock that only ever goes up never falls from a peak.
        # Max drawdown = 0 is the theoretical best case.
        cum = _returns([0.0, 0.1, 0.2, 0.3, 0.5])
        dd = calculate_max_drawdown(cum)
        self.assertAlmostEqual(dd["TEST"], 0.0, places=10)

    def test_drawdown_is_always_non_positive(self):
        # By definition: you can only be AT or BELOW a previous peak.
        # So max drawdown is always ≤ 0. It can never be positive.
        np.random.seed(7)
        cum_vals = np.random.normal(0, 0.05, 252).cumsum()
        cum = _returns(cum_vals)
        dd = calculate_max_drawdown(cum)
        self.assertLessEqual(dd["TEST"], 0.0)

    def test_deeper_trough_gives_worse_drawdown(self):
        # Falling to 0.7 from peak 1.2 is worse than falling to 0.9
        cum_shallow = _returns([0.0, 0.1, 0.2, -0.10])  # trough: 0.9, dd: -25%
        cum_deep    = _returns([0.0, 0.1, 0.2, -0.30])  # trough: 0.7, dd: -41.67%
        dd_shallow = calculate_max_drawdown(cum_shallow)
        dd_deep    = calculate_max_drawdown(cum_deep)
        self.assertLess(dd_deep["TEST"], dd_shallow["TEST"])


# ============================================================
# 7. Rolling Volatility
# ============================================================
class TestCalculateRollingVolatility(unittest.TestCase):
    """
    Formula tested: rolling_std(window) * sqrt(252)

    Unlike annualized volatility (one number for the whole period),
    rolling volatility tells you HOW risk changed over time.
    This is critical for spotting "volatility regimes" — e.g.
    the COVID crash in March 2020 shows up as a dramatic spike.
    """

    def test_output_shape_matches_input(self):
        # Rolling volatility should have the same rows and columns
        # as the input daily returns — just with NaN at the start.
        daily = pd.DataFrame({"A": [0.01] * 50, "B": [0.02] * 50})
        rolling = calculate_rolling_volatility(daily, window=10)
        self.assertEqual(rolling.shape, daily.shape)

    def test_first_window_minus_one_rows_are_nan(self):
        # With a window of 10, rows 0-8 are NaN (only 1-9 observations,
        # not enough to fill the window). Row 9 is the first valid value.
        window = 10
        daily = _returns([0.01] * 30)
        rolling = calculate_rolling_volatility(daily, window=window)
        self.assertTrue(rolling["TEST"].iloc[:window - 1].isna().all())
        self.assertFalse(rolling["TEST"].iloc[window - 1:].isna().any())

    def test_constant_returns_produce_zero_rolling_vol(self):
        # If returns are constant, std within every window = 0 → vol = 0
        daily = _returns([0.01] * 50)
        rolling = calculate_rolling_volatility(daily, window=5)
        non_nan = rolling["TEST"].dropna()
        self.assertTrue((non_nan.abs() < 1e-10).all())

    def test_rolling_vol_is_always_non_negative(self):
        # Standard deviation can never be negative.
        np.random.seed(99)
        daily = _returns(np.random.normal(0, 0.02, 100))
        rolling = calculate_rolling_volatility(daily, window=20)
        non_nan = rolling["TEST"].dropna()
        self.assertTrue((non_nan >= 0).all())


# ============================================================
# 8. calculate_all_metrics (integration test)
# ============================================================
class TestCalculateAllMetrics(unittest.TestCase):
    """
    Integration test: runs the master function end-to-end on
    a small synthetic dataset and verifies the output structure.

    This doesn't test the math (the unit tests above do that).
    It tests that the pipeline assembles correctly — all keys
    exist, all tickers are present, no unexpected NaN values
    in places where there should be real numbers.
    """

    def setUp(self):
        # Build a minimal 60-day synthetic price series for two tickers.
        # We fix the random seed so results are reproducible.
        np.random.seed(0)
        r_a = np.random.normal(0.001, 0.02, 60)
        r_b = np.random.normal(0.0005, 0.015, 60)
        self.prices = pd.DataFrame({
            "AAPL": 100 * np.cumprod(1 + r_a),
            "MSFT":  50 * np.cumprod(1 + r_b),
        })

    def test_all_expected_keys_are_present(self):
        result = calculate_all_metrics(self.prices, risk_free_rate=0.04, rolling_window=10)
        expected_keys = {
            "daily_returns", "cumulative_returns", "annualized_return",
            "annualized_volatility", "sharpe_ratio", "max_drawdown",
            "rolling_volatility",
        }
        self.assertEqual(set(result.keys()), expected_keys)

    def test_tickers_present_in_dataframe_outputs(self):
        result = calculate_all_metrics(self.prices, risk_free_rate=0.04, rolling_window=10)
        for key in ("daily_returns", "cumulative_returns", "rolling_volatility"):
            self.assertIn("AAPL", result[key].columns)
            self.assertIn("MSFT", result[key].columns)

    def test_tickers_present_in_series_outputs(self):
        result = calculate_all_metrics(self.prices, risk_free_rate=0.04, rolling_window=10)
        for key in ("annualized_return", "annualized_volatility", "sharpe_ratio", "max_drawdown"):
            self.assertIn("AAPL", result[key].index)
            self.assertIn("MSFT", result[key].index)

    def test_no_nan_in_scalar_metrics(self):
        result = calculate_all_metrics(self.prices, risk_free_rate=0.04, rolling_window=10)
        for key in ("annualized_return", "annualized_volatility", "sharpe_ratio", "max_drawdown"):
            self.assertFalse(result[key].isna().any(),
                             msg=f"NaN found in {key}")

    def test_max_drawdown_is_non_positive(self):
        result = calculate_all_metrics(self.prices, risk_free_rate=0.04, rolling_window=10)
        self.assertTrue((result["max_drawdown"] <= 0).all())


# ============================================================
# Entry point: run tests when file is executed directly
# ============================================================
if __name__ == "__main__":
    unittest.main(verbosity=2)
