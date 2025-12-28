"""
Backtesting module for 4D lottery predictions.
Evaluates prediction accuracy using walk-forward validation.
"""

from constants import FD_FIRST_PRIZE_CLASS, DEFAULT_PRIZE_WEIGHTS
from analyzer import (
    analyze_first_digit_weighted, bayesian_smoothing, 
    chi_square_test_uniform, select_digits_by_probability
)
from utils import get_last_n_draws


def backtest_digit_prediction(df, window_sizes=[12, 52], top_k_list=[1, 3, 5], 
                               weights=None, alpha=1.0):
    """
    Backtest digit prediction across multiple draws.
    
    Args:
        df: DataFrame with all historical draws
        window_sizes: List of window sizes to test (default: [12, 52])
        top_k_list: List of top-K values to test (default: [1, 3, 5])
        weights: Prize type weights (default: Top3=1.0, Starter=0.3, Consolation=0.3)
        alpha: Smoothing parameter for Bayesian smoothing
    
    Returns:
        dict: Backtest results for each window size
    """
    if weights is None:
        weights = DEFAULT_PRIZE_WEIGHTS
        
    unique_dates = df.index.unique().sort_values()
    
    if len(unique_dates) < max(window_sizes) + 10:
        print(f"Warning: Not enough draws ({len(unique_dates)}) for backtesting.")
        return {}
    
    results = {}
    
    for window_size in window_sizes:
        print(f"\nBacktesting with window size: {window_size} draws")
        
        window_results = {
            'window_size': window_size,
            'total_tests': 0,
            'accuracy': {k: {'correct': 0, 'total': 0} for k in top_k_list},
            'chi2_tests': {'uniform': 0, 'non_uniform': 0, 'total': 0}
        }
        
        # Start backtesting from window_size+1 to avoid look-ahead
        for i in range(window_size, len(unique_dates)):
            test_date = unique_dates[i]
            train_dates = unique_dates[i - window_size:i]
            
            # Get training data
            train_df = df[df.index.isin(train_dates)]
            
            # Get actual first digit for this draw's first prize
            test_df = df[df.index == test_date]
            first_prize_df = test_df[test_df['Prize Type'] == FD_FIRST_PRIZE_CLASS]
            
            if first_prize_df.empty:
                continue
            
            actual_first_digit = str(first_prize_df.iloc[0]['Prize Number']).strip()[0]
            if not actual_first_digit.isdigit():
                continue
            
            # Analyze training data
            weighted_counts = analyze_first_digit_weighted(train_df, weights)
            probabilities = bayesian_smoothing(weighted_counts, alpha)
            chi2_result = chi_square_test_uniform(weighted_counts)
            
            # Update chi-square test counts
            window_results['chi2_tests']['total'] += 1
            if chi2_result['is_uniform']:
                window_results['chi2_tests']['uniform'] += 1
            else:
                window_results['chi2_tests']['non_uniform'] += 1
            
            # Test predictions for different top_k values
            for top_k in top_k_list:
                predicted_digits = select_digits_by_probability(probabilities, top_k)
                window_results['accuracy'][top_k]['total'] += 1
                
                if actual_first_digit in predicted_digits:
                    window_results['accuracy'][top_k]['correct'] += 1
        
        # Calculate accuracy rates
        for top_k in top_k_list:
            if window_results['accuracy'][top_k]['total'] > 0:
                acc = window_results['accuracy'][top_k]['correct'] / window_results['accuracy'][top_k]['total']
                window_results['accuracy'][top_k]['rate'] = acc
        
        results[window_size] = window_results
    
    return results


def print_backtest_results(backtest_results):
    """
    Print backtest results in a formatted way.
    
    Args:
        backtest_results: Dictionary of backtest results
    """
    print("\n" + "=" * 80)
    print("BACKTEST RESULTS")
    print("=" * 80)
    
    for window_size, results in sorted(backtest_results.items()):
        print(f"\nWindow Size: {window_size} draws")
        print("-" * 80)
        
        # Chi-square test summary
        chi2 = results['chi2_tests']
        uniform_rate = chi2['uniform'] / chi2['total'] if chi2['total'] > 0 else 0
        print(f"Chi-square test: {chi2['uniform']}/{chi2['total']} ({uniform_rate*100:.1f}%) consistent with uniform")
        
        # Accuracy results
        print("\nAccuracy by Top-K:")
        for top_k in sorted(results['accuracy'].keys()):
            acc_data = results['accuracy'][top_k]
            if acc_data['total'] > 0:
                accuracy = acc_data['rate']
                baseline = top_k / 10.0  # Random baseline
                improvement = (accuracy - baseline) / baseline * 100 if baseline > 0 else 0
                print(f"  Top-{top_k}: {acc_data['correct']}/{acc_data['total']} = {accuracy*100:.1f}% "
                      f"(baseline: {baseline*100:.1f}%, improvement: {improvement:+.1f}%)")

