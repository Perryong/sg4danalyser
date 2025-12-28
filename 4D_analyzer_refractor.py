"""
Main 4D analyzer script - refactored version using SOC and DRY principles.
Orchestrates data fetching, analysis, filtering, and visualization.
"""

from datetime import datetime, timedelta
import pandas as pd

from constants import CACHE_6MONTHS_FILE, CACHE_1YEAR_FILE, OUTPUT_DIR, DEFAULT_PRIZE_WEIGHTS
from cache_manager import fetch_with_cache
from analyzer import (
    analyze_first_digit_by_prize_type, analyze_first_digit_weighted,
    bayesian_smoothing, chi_square_test_uniform, select_digits_by_probability,
    select_digits_priority_zero, select_digits_lowest_occurrence
)
from filter import generate_numbers_from_first_digits, filter_numbers_by_history
from utils import get_last_n_draws, save_results_to_file
from visualizer import (
    visualize_weighted_digit_counts, visualize_bayesian_probabilities,
    visualize_chi_square_tests, visualize_rolling_windows_comparison,
    visualize_backtest_results
)
from backtest import backtest_digit_prediction, print_backtest_results


def main_original():
    """
    Original main function to filter 4D numbers based on first digit analysis.
    Uses simple last 6 draws analysis.
    """
    print("=" * 60)
    print("Filter 4D Numbers: Based on First Digit Analysis")
    print("=" * 60)
    
    today = datetime.now()
    six_months_ago = today - timedelta(days=180)
    one_year_ago = today - timedelta(days=365)
    
    # Fetch past 6 months data (with caching)
    print("\nFetching past 6 months of 4D results (all prize categories)...")
    past_6_months_df = fetch_with_cache(
        six_months_ago, 
        today, 
        CACHE_6MONTHS_FILE, 
        cache_label="6 months data"
    )
    
    if past_6_months_df.empty:
        print("No data found for past 6 months. Exiting.")
        return
    
    # Get last 6 draws
    print("\n" + "=" * 60)
    print("Step 1: Getting last 6 draws")
    print("=" * 60)
    last_6_draws_df = get_last_n_draws(past_6_months_df, n=6)
    
    if last_6_draws_df.empty:
        print("No draws found. Exiting.")
        return
    
    unique_dates = last_6_draws_df.index.unique().sort_values(ascending=False)
    print(f"Found {len(unique_dates)} draws")
    for date in unique_dates:
        print(f"  - {date.strftime('%d %b %Y')}")
    
    # Step 2: Analyze first digit of top 3 prizes in last 6 draws
    print("\n" + "=" * 60)
    print("Step 2: Analyzing first digit of top 3 prizes (past 6 draws)")
    print("=" * 60)
    from constants import TOP_3_PRIZE_TYPES
    top3_first_digit_counts = analyze_first_digit_by_prize_type(last_6_draws_df, TOP_3_PRIZE_TYPES)
    print("First digit occurrence in top 3 prizes (past 6 draws):")
    for digit in sorted(top3_first_digit_counts.keys()):
        print(f"  Digit {digit}: {top3_first_digit_counts[digit]} occurrences")
    
    # Select digits with 0 occurrence in top 3 prizes (priority), otherwise use low occurrence threshold
    selected_digits_step1 = select_digits_priority_zero(top3_first_digit_counts)
    zero_occurrence_digits = [digit for digit, count in top3_first_digit_counts.items() if count == 0]
    if zero_occurrence_digits:
        print(f"\nSelected first digits from top 3 analysis (0 occurrence): {selected_digits_step1}")
    else:
        print(f"\nSelected first digits from top 3 analysis (low occurrence): {selected_digits_step1}")
    
    # Step 3: Analyze first digit occurrence across all prize types in last 6 draws
    print("\n" + "=" * 60)
    print("Step 3: Analyzing first digit occurrence across all prize types (past 6 draws)")
    print("=" * 60)
    all_prizes_first_digit_counts = analyze_first_digit_by_prize_type(last_6_draws_df, None)
    print("First digit occurrence across all prize types (past 6 draws):")
    for digit in sorted(all_prizes_first_digit_counts.keys()):
        print(f"  Digit {digit}: {all_prizes_first_digit_counts[digit]} occurrences")
    
    # Select digit(s) with the lowest occurrence rate across all prizes
    selected_digits_step2 = select_digits_lowest_occurrence(all_prizes_first_digit_counts)
    min_occurrence = min(all_prizes_first_digit_counts.values()) if all_prizes_first_digit_counts else 0
    print(f"\nSelected first digit(s) from all prizes analysis (lowest occurrence: {min_occurrence}): {selected_digits_step2}")
    
    # Combine selections: keep digits that are in either list (union)
    final_selected_digits = sorted(list(set(selected_digits_step1) | set(selected_digits_step2)))
    print(f"\nFinal selected first digits (combined from both analyses): {final_selected_digits}")
    
    # Step 4: Generate numbers based on selected first digits
    print("\n" + "=" * 60)
    print("Step 4: Generating numbers from selected first digits")
    print("=" * 60)
    generated_numbers = generate_numbers_from_first_digits(final_selected_digits)
    print(f"Generated {len(generated_numbers)} numbers from first digits: {final_selected_digits}")
    for digit in final_selected_digits:
        count = len([n for n in generated_numbers if n.startswith(digit)])
        print(f"  First digit {digit}: {count} numbers ({int(digit)*1000}-{int(digit)*1000+999})")
    
    # Fetch past 1 year data (with caching) for filtering
    print("\nFetching past 1 year of 4D results (all prize categories)...")
    past_1_year_df = fetch_with_cache(
        one_year_ago, 
        today, 
        CACHE_1YEAR_FILE, 
        cache_label="1 year data"
    )
    
    if past_1_year_df.empty:
        print("Warning: No data found for past 1 year. Will only filter by 6 months data.")
        past_1_year_df = pd.DataFrame(columns=['Date', 'Prize Number', 'Prize Type'])
    
    # Step 5: Filter generated numbers
    filtered_numbers, appeared_in_6_months, appeared_in_top3_1year, appeared_multiple_1year = filter_numbers_by_history(
        generated_numbers, past_6_months_df, past_1_year_df
    )
    
    if not filtered_numbers:
        print("\nNo numbers remaining after filtering!")
        return
    
    # Display summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Selected first digits: {final_selected_digits}")
    print(f"Total generated numbers: {len(generated_numbers)}")
    print(f"Numbers appeared in past 6 months (all prizes): {len(appeared_in_6_months)}")
    print(f"Numbers appeared in top 3 prizes (past 1 year): {len(appeared_in_top3_1year)}")
    print(f"Numbers appeared multiple times (past 1 year): {len(appeared_multiple_1year)}")
    print(f"Final filtered numbers: {len(filtered_numbers)}")
    
    # Save results
    metadata = {
        "Filtered 4D Numbers: Based on First Digit Analysis:": "",
        "Generated on": today.strftime('%d %b %Y %H:%M:%S'),
        "Last 6 draws analyzed": ", ".join([d.strftime('%d %b %Y') for d in unique_dates]),
        "Selected first digits": ", ".join(final_selected_digits),
        "Date range for filtering (6 months)": f"{six_months_ago.strftime('%d %b %Y')} to {today.strftime('%d %b %Y')}",
        "Date range for filtering (1 year)": f"{one_year_ago.strftime('%d %b %Y')} to {today.strftime('%d %b %Y')}",
        "Total generated numbers": str(len(generated_numbers)),
        "Numbers appeared in past 6 months (all prizes)": str(len(appeared_in_6_months)),
        "Numbers appeared in top 3 prizes (past 1 year)": str(len(appeared_in_top3_1year)),
        "Numbers appeared multiple times (past 1 year)": str(len(appeared_multiple_1year)),
        "Final filtered numbers": str(len(filtered_numbers))
    }
    
    text_file, csv_file = save_results_to_file(
        filtered_numbers, OUTPUT_DIR, "filtered_first_digit", metadata
    )
    
    print(f"\nResults saved to: {text_file}")
    print(f"Results also saved to: {csv_file}")
    
    # Display sample
    print("\n" + "=" * 60)
    print("Sample of filtered numbers (first 20):")
    print("=" * 60)
    for i in range(0, min(20, len(filtered_numbers)), 10):
        group = filtered_numbers[i:i+10]
        print("  ".join(group))
    
    return filtered_numbers


def main_improved(use_window_sizes=[12, 52], enable_backtest=True, top_k=3, alpha=1.0):
    """
    Improved main function using Bayesian smoothing, weighted analysis, and rolling windows.
    
    Args:
        use_window_sizes: List of window sizes to analyze (default: [12, 52])
        enable_backtest: Whether to run backtesting (default: True)
        top_k: Number of top digits to select based on probability (default: 3)
        alpha: Smoothing parameter for Bayesian smoothing (default: 1.0)
    """
    print("=" * 80)
    print("IMPROVED 4D FILTER: Bayesian Analysis with Rolling Windows")
    print("=" * 80)
    
    today = datetime.now()
    one_year_ago = today - timedelta(days=365)
    
    # Fetch data - need more data for longer windows
    print("\nFetching historical 4D results...")
    historical_df = fetch_with_cache(
        one_year_ago,
        today,
        CACHE_1YEAR_FILE,
        cache_label="1 year data"
    )
    
    if historical_df.empty:
        print("No data found. Exiting.")
        return
    
    print(f"Loaded {len(historical_df)} records from {len(historical_df.index.unique())} draws")
    
    # Analyze with different window sizes
    window_analyses = {}
    
    for window_size in use_window_sizes:
        print(f"\n{'=' * 80}")
        print(f"ANALYSIS: Window Size = {window_size} draws")
        print('=' * 80)
        
        # Get last N draws
        window_df = get_last_n_draws(historical_df, n=window_size)
        
        if window_df.empty or len(window_df.index.unique()) < window_size:
            print(f"Not enough data for window size {window_size}. Skipping.")
            continue
        
        # Weighted analysis
        weighted_counts = analyze_first_digit_weighted(window_df, DEFAULT_PRIZE_WEIGHTS)
        print(f"\nWeighted digit counts (Top3=1.0, Starter/Consolation=0.3):")
        for digit in sorted(weighted_counts.keys()):
            print(f"  Digit {digit}: {weighted_counts[digit]:.2f}")
        
        # Bayesian smoothing
        probabilities = bayesian_smoothing(weighted_counts, alpha)
        print(f"\nBayesian-smoothed probabilities (α={alpha}):")
        sorted_probs = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
        for digit, prob in sorted_probs:
            print(f"  Digit {digit}: {prob:.4f} ({prob*100:.2f}%)")
        
        # Chi-square test
        chi2_result = chi_square_test_uniform(weighted_counts)
        print(f"\nChi-square test for uniformity:")
        print(f"  Chi-square statistic: {chi2_result['chi2']:.4f}")
        print(f"  P-value: {chi2_result['pvalue']:.4f}")
        print(f"  Expected per digit: {chi2_result['expected_per_digit']:.2f}")
        if chi2_result['is_uniform']:
            print(f"  Result: Distribution is CONSISTENT with uniform (p > 0.05)")
            print(f"  Warning: No significant bias detected - predictions may be unreliable")
        else:
            print(f"  Result: Distribution is NOT uniform (p <= 0.05)")
            print(f"  Significant bias detected - may be predictive")
        
        # Select top K digits
        selected_digits = select_digits_by_probability(probabilities, top_k)
        print(f"\nSelected top-{top_k} digits by probability: {selected_digits}")
        
        window_analyses[window_size] = {
            'weighted_counts': weighted_counts,
            'probabilities': probabilities,
            'chi2_result': chi2_result,
            'selected_digits': selected_digits
        }
    
    # Generate visualizations
    print("\nGenerating visualizations...")
    visualize_weighted_digit_counts(window_analyses, OUTPUT_DIR)
    visualize_bayesian_probabilities(window_analyses, OUTPUT_DIR)
    visualize_chi_square_tests(window_analyses, OUTPUT_DIR)
    visualize_rolling_windows_comparison(window_analyses, OUTPUT_DIR)
    
    # Run backtesting if enabled
    if enable_backtest:
        print(f"\n{'=' * 80}")
        print("BACKTESTING")
        print('=' * 80)
        backtest_results = backtest_digit_prediction(
            historical_df,
            window_sizes=use_window_sizes,
            top_k_list=[1, 3, 5],
            weights=DEFAULT_PRIZE_WEIGHTS,
            alpha=alpha
        )
        print_backtest_results(backtest_results)
        
        # Visualize backtest results
        visualize_backtest_results(backtest_results, OUTPUT_DIR)
    
    # Use most appropriate window size for final selection
    # Prefer windows with non-uniform distribution if available
    best_window = None
    for window_size in sorted(use_window_sizes, reverse=True):
        if window_size in window_analyses:
            chi2_result = window_analyses[window_size]['chi2_result']
            if not chi2_result['is_uniform']:
                best_window = window_size
                break
    
    # If all are uniform, use largest window
    if best_window is None:
        best_window = max(use_window_sizes)
    
    print(f"\n{'=' * 80}")
    print(f"FINAL SELECTION: Using window size {best_window} draws")
    print('=' * 80)
    
    final_analysis = window_analyses[best_window]
    final_selected_digits = final_analysis['selected_digits']
    
    print(f"Selected digits: {final_selected_digits}")
    
    # Generate numbers and filter
    generated_numbers = generate_numbers_from_first_digits(final_selected_digits)
    print(f"Generated {len(generated_numbers)} numbers")
    
    # Apply standard filters
    six_months_ago = today - timedelta(days=180)
    past_6_months_df = fetch_with_cache(
        six_months_ago,
        today,
        CACHE_6MONTHS_FILE,
        cache_label="6 months data"
    )
    
    filtered_numbers, _, _, _ = filter_numbers_by_history(
        generated_numbers, past_6_months_df, historical_df
    )
    
    # Save results
    metadata = {
        "Improved 4D Filter: Bayesian Analysis with Rolling Windows:": "",
        "Generated on": today.strftime('%d %b %Y %H:%M:%S'),
        "Window sizes analyzed": ", ".join(map(str, use_window_sizes)),
        "Selected window": f"{best_window} draws",
        "Selected digits": ", ".join(final_selected_digits),
        "Final filtered numbers": str(len(filtered_numbers))
    }
    
    text_file, csv_file = save_results_to_file(
        filtered_numbers, OUTPUT_DIR, "filtered_improved", metadata
    )
    
    print(f"\nResults saved to: {text_file}")
    print(f"CSV saved to: {csv_file}")
    
    return filtered_numbers


if __name__ == "__main__":
    # Use improved method by default, but old method still available
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--old':
        results = main_original()
    else:
        results = main_improved()

