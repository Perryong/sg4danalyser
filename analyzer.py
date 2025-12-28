"""
Statistical analysis module for 4D lottery number analysis.
Includes Bayesian smoothing, chi-square tests, and digit selection methods.
"""

from scipy import stats
from constants import (
    FD_FIRST_PRIZE_CLASS, FD_SECOND_PRIZE_CLASS, FD_THIRD_PRIZE_CLASS,
    FD_STARTER_PRIZE_CLASS, FD_CONSOLATION_PRIZE_CLASS,
    DEFAULT_PRIZE_WEIGHTS, TOP_3_PRIZE_TYPES
)


def extract_first_digits(df, prize_types=None):
    """
    Extract first digits from prize numbers in DataFrame.
    
    Args:
        df: DataFrame with 'Prize Number' column
        prize_types: Optional list of prize types to filter. If None, uses all.
    
    Returns:
        list: List of first digits (as strings)
    """
    filtered_df = df if prize_types is None else df[df['Prize Type'].isin(prize_types)]
    
    first_digits = []
    for prize_num in filtered_df['Prize Number']:
        if len(str(prize_num)) >= 1:
            first_digit = str(prize_num).strip()[0]
            if first_digit.isdigit():
                first_digits.append(first_digit)
    
    return first_digits


def count_digits(first_digits):
    """
    Count occurrences of each digit (0-9).
    
    Args:
        first_digits: List of first digits (as strings)
    
    Returns:
        dict: Dictionary with digit (0-9) as key and count as value
    """
    digit_counts = {str(d): 0 for d in range(10)}
    for digit in first_digits:
        if digit in digit_counts:
            digit_counts[digit] += 1
    return digit_counts


def analyze_first_digit_weighted(df, weights=None):
    """
    Analyze first digit occurrence with weighted prize types.
    
    Args:
        df: DataFrame with draws data
        weights: Dict of prize type weights (default: Top3=1.0, Starter=0.3, Consolation=0.3)
    
    Returns:
        dict: Dictionary with first digit (0-9) as key and weighted count as value
    """
    if weights is None:
        weights = DEFAULT_PRIZE_WEIGHTS
    
    weighted_counts = {str(d): 0.0 for d in range(10)}
    
    for _, row in df.iterrows():
        prize_type = row['Prize Type']
        prize_num = str(row['Prize Number']).strip()
        
        if len(prize_num) >= 1 and prize_num[0].isdigit():
            first_digit = prize_num[0]
            weight = weights.get(prize_type, 1.0)
            weighted_counts[first_digit] += weight
    
    return weighted_counts


def analyze_first_digit_by_prize_type(df, prize_types=None):
    """
    Analyze first digit occurrence for specific prize types.
    If prize_types is None, analyzes all prize types.
    
    Args:
        df: DataFrame with draws data
        prize_types: List of prize type classes to analyze (None = all prize types)
    
    Returns:
        dict: Dictionary with first digit (0-9) as key and count as value
    """
    first_digits = extract_first_digits(df, prize_types)
    return count_digits(first_digits)


# Legacy function names for backward compatibility
def analyze_first_digit_top3_prizes(df):
    """Analyze first digit occurrence in top 3 prizes (legacy function)."""
    return analyze_first_digit_by_prize_type(df, TOP_3_PRIZE_TYPES)


def analyze_first_digit_all_prizes(df):
    """Analyze first digit occurrence across all prize types (legacy function)."""
    return analyze_first_digit_by_prize_type(df, None)


def bayesian_smoothing(digit_counts, alpha=1.0):
    """
    Apply Bayesian smoothing (Dirichlet-Multinomial) to digit counts.
    
    P(d) = (counts[d] + α) / (N + 10α)
    
    Args:
        digit_counts: Dictionary with digit as key and count as value
        alpha: Smoothing parameter (default: 1.0, Laplace smoothing)
    
    Returns:
        dict: Dictionary with digit as key and probability as value
    """
    total_count = sum(digit_counts.values())
    n_digits = len(digit_counts)
    denominator = total_count + n_digits * alpha
    
    probabilities = {}
    for digit in digit_counts:
        probabilities[digit] = (digit_counts[digit] + alpha) / denominator
    
    return probabilities


def chi_square_test_uniform(digit_counts):
    """
    Test if digit distribution deviates from uniform using chi-square test.
    
    Args:
        digit_counts: Dictionary with digit as key and count as value
    
    Returns:
        dict: Dictionary with 'chi2', 'pvalue', 'is_uniform', 'expected_per_digit', etc.
    """
    observed = [digit_counts.get(str(d), 0) for d in range(10)]
    total = sum(observed)
    expected_per_digit = total / 10.0 if total > 0 else 0
    
    if total == 0:
        return {
            'chi2': 0,
            'pvalue': 1.0,
            'is_uniform': True,
            'expected_per_digit': 0,
            'degrees_of_freedom': 9
        }
    
    expected = [expected_per_digit] * 10
    chi2, pvalue = stats.chisquare(observed, expected)
    
    # Use 0.05 significance level
    is_uniform = pvalue > 0.05
    
    return {
        'chi2': chi2,
        'pvalue': pvalue,
        'is_uniform': is_uniform,
        'expected_per_digit': expected_per_digit,
        'degrees_of_freedom': 9,
        'observed': observed,
        'expected': expected
    }


def select_digits_by_probability(probabilities, top_k=3):
    """
    Select top K digits by probability.
    
    Args:
        probabilities: Dictionary with digit as key and probability as value
        top_k: Number of top digits to select
    
    Returns:
        list: List of selected first digits (sorted by probability, descending)
    """
    sorted_digits = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
    selected = [digit for digit, prob in sorted_digits[:top_k]]
    return selected


def select_low_occurrence_digits(digit_counts, min_count_threshold=None):
    """
    Select first digits with low or zero occurrence.
    If min_count_threshold is None, selects digits with below-average occurrence.
    
    Args:
        digit_counts: Dictionary with digit as key and count as value
        min_count_threshold: Maximum count threshold (None = use average)
    
    Returns:
        list: List of selected first digits (as strings)
    """
    if min_count_threshold is None:
        # Calculate average occurrence
        total_counts = sum(digit_counts.values())
        if total_counts == 0:
            # If no counts, select all digits
            return [str(d) for d in range(10)]
        avg_count = total_counts / len(digit_counts)
        min_count_threshold = avg_count
    
    # Select digits with count <= threshold
    selected_digits = [
        digit for digit, count in digit_counts.items() 
        if count <= min_count_threshold
    ]
    
    # If no digits selected (all above threshold), select the lowest ones
    if not selected_digits:
        sorted_digits = sorted(digit_counts.items(), key=lambda x: x[1])
        # Select at least half of the digits with lowest counts
        num_to_select = max(1, len(digit_counts) // 2)
        selected_digits = [digit for digit, _ in sorted_digits[:num_to_select]]
    
    return sorted(selected_digits)


def select_digits_priority_zero(digit_counts):
    """
    Select first digits with priority on zero occurrence.
    If any digits have 0 occurrence, select those digits.
    Otherwise, use the standard low occurrence selection method.
    
    Args:
        digit_counts: Dictionary with digit as key and count as value
    
    Returns:
        list: List of selected first digits (as strings)
    """
    # First, check if any digits have 0 occurrence
    zero_occurrence_digits = [
        digit for digit, count in digit_counts.items() 
        if count == 0
    ]
    
    if zero_occurrence_digits:
        # If digits with 0 occurrence exist, use those
        return sorted(zero_occurrence_digits)
    else:
        # Otherwise, use the standard low occurrence method
        return select_low_occurrence_digits(digit_counts)


def select_digits_lowest_occurrence(digit_counts):
    """
    Select only the digit(s) with the lowest occurrence rate.
    If multiple digits have the same minimum occurrence, select all of them.
    
    Args:
        digit_counts: Dictionary with digit as key and count as value
    
    Returns:
        list: List of selected first digits (as strings) with lowest occurrence
    """
    if not digit_counts:
        return []
    
    # Find the minimum occurrence count
    min_count = min(digit_counts.values())
    
    # Select all digits with the minimum occurrence count
    selected_digits = [
        digit for digit, count in digit_counts.items() 
        if count == min_count
    ]
    
    return sorted(selected_digits)

