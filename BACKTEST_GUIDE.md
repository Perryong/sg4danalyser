# How to Interpret Backtest Results

## What is Backtesting?

Backtesting evaluates how well your prediction model would have performed on historical data. It uses **walk-forward validation** to ensure realistic testing - meaning it only uses data available **before** each prediction (no look-ahead bias).

## How Backtesting Works

### 1. Walk-Forward Validation Process

For each draw in your historical data (starting from draw #window_size+1):

1. **Training Phase**: Uses the previous N draws (e.g., 12 or 52 draws) to:
   - Calculate weighted digit frequencies
   - Apply Bayesian smoothing to get probabilities
   - Select top-K digits with highest probabilities

2. **Testing Phase**: 
   - Makes a prediction based on the training data
   - Checks if the actual first digit of the 1st prize is in your predicted top-K digits
   - Records whether the prediction was correct

### 2. Metrics Calculated

The backtest calculates three main metrics:

#### A. Accuracy by Top-K

For each Top-K prediction (Top-1, Top-3, Top-5):

- **Accuracy Rate**: Percentage of correct predictions
  - Formula: `(correct predictions / total predictions) × 100%`
  
- **Baseline (Random)**: Expected accuracy if predictions were random
  - Top-1: 10% (1 digit out of 10)
  - Top-3: 30% (3 digits out of 10)
  - Top-5: 50% (5 digits out of 10)

- **Improvement**: How much better (or worse) than random
  - Formula: `((accuracy - baseline) / baseline) × 100%`
  - Positive = better than random
  - Negative = worse than random
  - 0% = same as random

#### B. Chi-Square Test Distribution

Tracks how often the digit distribution was uniform vs non-uniform during backtesting:
- **Uniform**: Distribution was consistent with random (p > 0.05)
- **Non-Uniform**: Distribution showed significant bias (p ≤ 0.05)

#### C. Total Tests

The number of draws tested (total available draws minus window size)

## Interpreting Results

### Example Output

```
Window Size: 12 draws
--------------------------------------------------------------------------------
Chi-square test: 45/100 (45.0%) consistent with uniform

Accuracy by Top-K:
  Top-1: 15/100 = 15.0% (baseline: 10.0%, improvement: +50.0%)
  Top-3: 28/100 = 28.0% (baseline: 30.0%, improvement: -6.7%)
  Top-5: 48/100 = 48.0% (baseline: 50.0%, improvement: -4.0%)
```

### What This Means:

#### Chi-Square Test Results

- **45% uniform**: In 45 out of 100 tests, the distribution was random (no bias detected)
- **55% non-uniform**: In 55 tests, there was significant bias
- **Interpretation**: Mixed results - sometimes there's bias, sometimes it's random

#### Top-1 Accuracy (15.0%)

- **Your accuracy**: 15 correct out of 100 predictions = 15%
- **Baseline (random)**: 10%
- **Improvement**: +50% better than random
- **Interpretation**: ✅ **Good** - You're 50% better than random guessing

#### Top-3 Accuracy (28.0%)

- **Your accuracy**: 28 correct out of 100 = 28%
- **Baseline (random)**: 30%
- **Improvement**: -6.7% (worse than random)
- **Interpretation**: ⚠️ **Poor** - Actually worse than random guessing

#### Top-5 Accuracy (48.0%)

- **Your accuracy**: 48 correct out of 100 = 48%
- **Baseline (random)**: 50%
- **Improvement**: -4.0% (slightly worse)
- **Interpretation**: ⚠️ **Poor** - Slightly worse than random

## How to Determine if Results are Good

### ✅ Good Backtest Results

1. **Top-K accuracy consistently beats baseline**
   - Top-1: > 10% (ideally > 15%)
   - Top-3: > 30% (ideally > 35%)
   - Top-5: > 50% (ideally > 55%)

2. **Positive improvement percentages** across all Top-K values

3. **Higher non-uniform percentage** (> 50%) in chi-square tests
   - Indicates the model is finding real patterns

4. **Consistent performance** across different window sizes

### ⚠️ Poor Backtest Results

1. **Accuracy close to or below baseline**
   - Top-1: ≤ 10%
   - Top-3: ≤ 30%
   - Top-5: ≤ 50%

2. **Negative improvement percentages**
   - Worse than random guessing

3. **High uniform percentage** (> 80%) in chi-square tests
   - Suggests no real patterns detected

4. **Inconsistent or highly variable results**
   - Large swings in accuracy

### 📊 What to Look For

#### Comparing Window Sizes

If you test multiple window sizes (e.g., 12 and 52 draws):

- **Smaller window (12)**: May be more sensitive to recent trends
  - Better if patterns change quickly
  - Risk of overfitting to noise

- **Larger window (52)**: More stable, captures longer-term patterns
  - Better if patterns are persistent
  - Risk of missing recent changes

**Best Practice**: Choose the window size with:
- Highest accuracy improvement
- Most consistent performance
- Lower uniform percentage (more pattern detection)

#### Comparing Top-K Values

- **Top-1**: Most strict test (must predict exact digit)
  - Best indicator of model quality
  - Most difficult to beat baseline

- **Top-3**: Balanced test (predicts 30% of digits)
  - Practical for number selection
  - Good middle ground

- **Top-5**: Easiest test (predicts 50% of digits)
  - Less informative
  - Should still beat baseline

**Good Sign**: If Top-1 shows positive improvement, the model is finding real patterns.

## Realistic Expectations

### Lottery Reality Check

**Important**: Lotteries are designed to be random. It's statistically unlikely to find persistent predictive patterns. Good backtest results don't guarantee future success.

### What "Good" Results Actually Mean

1. **Historical Pattern Detection**: The model found patterns in past data
2. **No Guarantee**: These patterns may not persist in future draws
3. **Small Edge**: Even a 5-10% improvement over random is significant
4. **Statistical Noise**: Some "patterns" may be due to randomness

### Red Flags

🚨 **Be suspicious if**:
- Accuracy improvements > 50% (likely overfitting or luck)
- Results vary wildly between runs
- Very high accuracy (e.g., Top-1 > 20%) on lottery data
- Perfect or near-perfect predictions

## How to Use Backtest Results

### Decision Making

1. **If results are good** (consistently beat baseline):
   - Model shows promise for historical data
   - Consider using it with caution
   - Continue monitoring performance

2. **If results are poor** (at or below baseline):
   - Model is not finding useful patterns
   - May be better to use random selection
   - Consider adjusting parameters or methods

3. **If results are mixed**:
   - Some window sizes/parameters may work better
   - Test different configurations
   - Focus on what works consistently

### Parameter Tuning

Use backtest results to optimize:

- **Window sizes**: Test [12, 24, 52, 100] to find optimal
- **Top-K selection**: Determine best K value (default: 3)
- **Alpha (smoothing)**: Test different α values (default: 1.0)
- **Prize weights**: Adjust weights for different prize types

### Validation

- Run backtests on multiple time periods
- Check if results are consistent across different dates
- Use out-of-sample testing (don't use all data for training)

## Visualization

The backtest also generates visualizations in `output/backtest_results_YYYYMMDD.png`:

1. **Top Panel**: Bar chart showing accuracy by Top-K for each window size
   - Compare your accuracy (bars) vs baseline (dashed line)
   - Bars above baseline = good
   - Bars below baseline = poor

2. **Bottom Panel**: Chi-square test distribution
   - Green bars = uniform (random) distributions
   - Red bars = non-uniform (biased) distributions
   - More red = more pattern detection

## Summary

### Key Questions to Ask

1. **Does the model beat random?**
   - Check if accuracy > baseline for all Top-K values

2. **Is it consistent?**
   - Do multiple window sizes show similar results?

3. **How much better is it?**
   - Look at improvement percentages
   - +20-50% improvement is meaningful

4. **Are patterns real?**
   - Check chi-square test (more non-uniform = better)
   - Be wary of overfitting

### Bottom Line

**Good backtest results** = Model found patterns in historical data that beat random guessing. This suggests the approach may have value, but **does not guarantee** future performance. Use results to guide decisions, but maintain realistic expectations.

**Poor backtest results** = Model is not finding useful patterns. Consider alternative approaches or accept that lottery numbers may be effectively random.

