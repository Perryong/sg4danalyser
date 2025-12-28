"""
Filtering module for 4D lottery numbers.
Handles filtering logic for generated numbers based on historical appearances.
"""

from constants import TOP_3_PRIZE_TYPES


def filter_numbers_by_history(numbers, past_6_months_df, past_1_year_df):
    """
    Filter numbers by removing those that:
    1. Appeared in any prize category in past 6 months
    2. Appeared in top 3 prizes (First, Second, Third) within one year
    3. Appeared more than once within one year
    
    Args:
        numbers: Set or list of 4D numbers to filter
        past_6_months_df: DataFrame with past 6 months data
        past_1_year_df: DataFrame with past 1 year data
    
    Returns:
        tuple: (filtered_numbers, appeared_in_6_months, appeared_in_top3_1year, appeared_multiple_1year)
            - filtered_numbers: List of filtered numbers
            - appeared_in_6_months: List of numbers that appeared in past 6 months
            - appeared_in_top3_1year: List of numbers that appeared in top 3 prizes (past 1 year)
            - appeared_multiple_1year: List of numbers that appeared multiple times (past 1 year)
    """
    # Convert to set for efficient operations
    numbers_set = set(numbers) if not isinstance(numbers, set) else numbers
    
    print("=" * 60)
    print(f"Filtering {len(numbers_set)} numbers")
    print("=" * 60)
    
    # Step 1: Filter out numbers that appeared in past 6 months (all prize categories)
    print("\nStep 1: Filtering by past 6 months (all prize categories)")
    winning_numbers_6_months = set(past_6_months_df['Prize Number'].unique())
    print(f"Total unique winning numbers in past 6 months: {len(winning_numbers_6_months)}")
    
    appeared_in_6_months = sorted([num for num in numbers_set if num in winning_numbers_6_months])
    print(f"Generated numbers that appeared in past 6 months: {len(appeared_in_6_months)}")
    
    # First filter: remove numbers from past 6 months
    filtered_after_6_months = numbers_set - winning_numbers_6_months
    print(f"Numbers remaining after 6-month filter: {len(filtered_after_6_months)}")
    
    # Step 2: Filter out numbers that appeared in top 3 prizes in past 1 year
    print("\nStep 2: Filtering by top 3 prizes in past 1 year")
    appeared_in_top3_1year = []
    if not past_1_year_df.empty:
        top_3_prizes_df = past_1_year_df[past_1_year_df['Prize Type'].isin(TOP_3_PRIZE_TYPES)]
        top_3_numbers_1_year = set(top_3_prizes_df['Prize Number'].unique())
        print(f"Total unique top 3 prize numbers in past 1 year: {len(top_3_numbers_1_year)}")
        
        appeared_in_top3_1year = sorted([num for num in filtered_after_6_months if num in top_3_numbers_1_year])
        print(f"Generated numbers that appeared in top 3 prizes (past 1 year): {len(appeared_in_top3_1year)}")
        
        # Second filter: remove top 3 prize numbers from past 1 year
        filtered_after_top3 = filtered_after_6_months - top_3_numbers_1_year
        print(f"Numbers remaining after top 3 filter: {len(filtered_after_top3)}")
    else:
        print("No past 1 year data available, skipping top 3 filter")
        filtered_after_top3 = filtered_after_6_months
    
    # Step 3: Filter out numbers that appeared more than once in past 1 year
    print("\nStep 3: Filtering by multiple appearances in past 1 year")
    appeared_multiple_1year = []
    if not past_1_year_df.empty:
        # Count occurrences of each number in past 1 year
        number_counts = past_1_year_df['Prize Number'].value_counts()
        numbers_appeared_multiple = set(number_counts[number_counts > 1].index)
        print(f"Total numbers that appeared more than once in past 1 year: {len(numbers_appeared_multiple)}")
        
        appeared_multiple_1year = sorted([num for num in filtered_after_top3 if num in numbers_appeared_multiple])
        print(f"Generated numbers that appeared multiple times (past 1 year): {len(appeared_multiple_1year)}")
        
        # Third filter: remove numbers that appeared multiple times
        filtered_numbers = filtered_after_top3 - numbers_appeared_multiple
        print(f"Final filtered numbers: {len(filtered_numbers)}")
    else:
        print("No past 1 year data available, skipping multiple appearances filter")
        filtered_numbers = filtered_after_top3
    
    # Convert to sorted list for return
    filtered_numbers = sorted(filtered_numbers)
    
    return filtered_numbers, appeared_in_6_months, appeared_in_top3_1year, appeared_multiple_1year


def generate_numbers_from_first_digits(first_digits):
    """
    Generate all 4D numbers based on selected first digits.
    For example, if first digit is '1', generates 1000-1999.
    
    Args:
        first_digits: List of first digits (as strings, e.g., ['0', '1', '2'])
    
    Returns:
        set: Set of generated 4D numbers as strings (e.g., {'1000', '1001', ...})
    """
    generated_numbers = set()
    
    for first_digit in first_digits:
        # Generate all numbers with this first digit (0000-9999)
        start_num = int(first_digit) * 1000
        end_num = start_num + 999
        
        for num in range(start_num, end_num + 1):
            generated_numbers.add(str(num).zfill(4))
    
    return generated_numbers

