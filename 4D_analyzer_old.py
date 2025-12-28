"""
Script to filter 4D numbers based on first digit analysis:
1. Check the first digit of top 3 prizes (First, Second, Third) in the past 6 draws
2. Keep first digits that never appeared or have low occurrence
3. Check the first digit occurrence rate across all prize types (First, Second, Third, 
   Consolation, Starter) in the past 6 draws
4. Keep first digits with lower occurrence
5. Generate numbers based on selected first digits (e.g., if digit is 1, generate 1000-1999)
6. From generated numbers, filter out:
   - Numbers that appeared in any prize category in the past 6 months
   - Numbers that appeared in top 3 prizes within one year
   - Numbers that appeared more than once within one year
"""

from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import pickle
import os

# Constants
FD_DRAW_LIST_URL = 'http://www.singaporepools.com.sg/DataFileArchive/Lottery/Output/fourd_result_draw_list_en.html'
FD_RESULT_URL = 'http://www.singaporepools.com.sg/en/product/Pages/4d_results.aspx?sppl='

PARSER_NAME = 'html.parser'
SPPL_ATTR = 'querystring'
SPPL_TAG = 'option'

DT_FORMAT = '%d %b %Y'
DRAW_DATE_CLASS = 'drawDate'

FD_FIRST_PRIZE_CLASS = 'tdFirstPrize'
FD_SECOND_PRIZE_CLASS = 'tdSecondPrize'
FD_THIRD_PRIZE_CLASS = 'tdThirdPrize'
FD_STARTER_PRIZE_CLASS = 'tbodyStarterPrizes'
FD_CONSOLATION_PRIZE_CLASS = 'tbodyConsolationPrizes'

FD_STARTER_PRIZE_CSS_SEL = ' '.join(['.' + FD_STARTER_PRIZE_CLASS, 'td'])
FD_CONSOLAION_PRIZE_CSS_SEL = ' '.join(['.' + FD_CONSOLATION_PRIZE_CLASS, 'td'])

LOSE = 'Lose'

# Cache file paths
CACHE_DIR = 'cache'
CACHE_6MONTHS_FILE = os.path.join(CACHE_DIR, 'fd_results_6months.pkl')
CACHE_1YEAR_FILE = os.path.join(CACHE_DIR, 'fd_results_1year.pkl')

# Output directory for results
OUTPUT_DIR = 'output'


def load_cache(cache_file):
    """
    Load cached data from file.
    
    Args:
        cache_file: Path to cache file
    
    Returns:
        tuple: (DataFrame, last_date) or (None, None) if cache doesn't exist
    """
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
                df = cache_data.get('dataframe', None)
                last_date = cache_data.get('last_date', None)
                if df is not None and not df.empty:
                    # Convert index back to datetime if it's stored as string
                    if isinstance(df.index[0], str):
                        df.index = pd.to_datetime(df.index)
                    return df, last_date
        except Exception as e:
            print(f"Error loading cache: {e}")
            return None, None
    return None, None


def save_cache(cache_file, df, last_date):
    """
    Save data to cache file.
    
    Args:
        cache_file: Path to cache file
        df: DataFrame to cache
        last_date: Last date in the DataFrame
    """
    # Create cache directory if it doesn't exist
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    
    try:
        cache_data = {
            'dataframe': df,
            'last_date': last_date,
            'cached_at': datetime.now()
        }
        with open(cache_file, 'wb') as f:
            pickle.dump(cache_data, f)
        print(f"Cache saved to {cache_file}")
    except Exception as e:
        print(f"Error saving cache: {e}")


def fetch_fd_results_with_cache(date_from, date_to, cache_file, cache_label=""):
    """
    Fetch 4D results with caching support.
    If cache exists and contains data up to today, use cache.
    Otherwise, fetch only new data and append to cache.
    
    Args:
        date_from: Start date (datetime)
        date_to: End date (datetime)
        cache_file: Path to cache file
        cache_label: Label for cache (for display purposes)
    
    Returns:
        pd.DataFrame: DataFrame containing 4D results
    """
    today = datetime.now().date()
    
    # Try to load cache
    cached_df, cached_last_date = load_cache(cache_file)
    
    if cached_df is not None and not cached_df.empty:
        # Ensure index is DatetimeIndex
        if not isinstance(cached_df.index, pd.DatetimeIndex):
            cached_df.index = pd.to_datetime(cached_df.index)
        
        # Get date range from cached data
        min_cached_date = cached_df.index.min().date()
        max_cached_date = cached_df.index.max().date()
        
        print(f"\nCache found for {cache_label}")
        print(f"  Cached data range: {min_cached_date} to {max_cached_date}")
        print(f"  Today's date: {today}")
        
        if max_cached_date >= today:
            print(f"  Cache is up to date! Using cached data.")
            # Filter cached data to requested date range
            mask = (cached_df.index >= pd.Timestamp(date_from)) & (cached_df.index <= pd.Timestamp(date_to))
            filtered_df = cached_df[mask].copy()
            print(f"  Returning {len(filtered_df)} records from cache")
            return filtered_df
        else:
            # Cache exists but needs updating - fetch only new data
            print(f"  Cache needs updating. Fetching new data from {(max_cached_date + timedelta(days=1)).strftime('%d %b %Y')} to {date_to.strftime('%d %b %Y')}")
            fetch_from = max_cached_date + timedelta(days=1)
            # Ensure fetch_from is not before date_from
            if fetch_from < date_from.date():
                fetch_from = date_from.date()
            
            new_df = fetch_fd_results(pd.Timestamp(fetch_from), date_to)
            
            if not new_df.empty:
                # Combine cached and new data
                combined_df = pd.concat([cached_df, new_df])
                # Remove duplicates (in case of overlap) - keep the last occurrence
                combined_df = combined_df[~combined_df.index.duplicated(keep='last')]
                combined_df = combined_df.sort_index()
                
                # Update cache
                new_max_date = combined_df.index.max().date()
                save_cache(cache_file, combined_df, new_max_date)
                
                # Filter to requested date range
                mask = (combined_df.index >= pd.Timestamp(date_from)) & (combined_df.index <= pd.Timestamp(date_to))
                filtered_df = combined_df[mask].copy()
                print(f"  Combined cache and new data: {len(filtered_df)} total records")
                return filtered_df
            else:
                print(f"  No new data found. Using cached data.")
                # Filter cached data to requested date range
                mask = (cached_df.index >= pd.Timestamp(date_from)) & (cached_df.index <= pd.Timestamp(date_to))
                filtered_df = cached_df[mask].copy()
                return filtered_df
    else:
        # No cache exists - fetch all data
        print(f"\nNo cache found for {cache_label}. Fetching all data...")
        df = fetch_fd_results(date_from, date_to)
        
        if not df.empty:
            # Save to cache
            max_date = df.index.max().date() if hasattr(df.index.max(), 'date') else pd.to_datetime(df.index.max()).date()
            save_cache(cache_file, df, max_date)
        
        return df


def fetch_fd_results(date_from, date_to):
    """
    Fetch 4D results for a specified date range.
    
    Args:
        date_from: Start date (datetime)
        date_to: End date (datetime)
    
    Returns:
        pd.DataFrame: DataFrame containing 4D results
    """
    print(f"Fetching 4D results from {date_from.strftime('%d %b %Y')} to {date_to.strftime('%d %b %Y')}")
    
    # Get 4D Draw List
    print("Fetching draw list...")
    fd_draw_list_page = requests.get(FD_DRAW_LIST_URL)
    fd_draw_list_soup = BeautifulSoup(fd_draw_list_page.content, PARSER_NAME)
    fd_sppl_ids = [draw.get(SPPL_ATTR).rpartition('=')[2] for draw in fd_draw_list_soup.find_all(SPPL_TAG)]
    
    # Iterate through 4D Draw List to Consolidate 4D Results
    fd_result_list = []
    draws_processed = 0
    draws_in_range = 0
    
    for fd_sppl_id in fd_sppl_ids:
        try:
            fd_result_page = requests.get(FD_RESULT_URL + fd_sppl_id)
            fd_result_soup = BeautifulSoup(fd_result_page.content, PARSER_NAME)
            
            # Extract draw date
            draw_date_elements = fd_result_soup.find_all(class_=DRAW_DATE_CLASS)
            if not draw_date_elements:
                continue
                
            fd_result_dt = datetime.strptime(
                draw_date_elements[0].get_text().rpartition(', ')[2], 
                DT_FORMAT
            )
            
            # Check if draw date is within range
            if fd_result_dt < date_from:
                # Since draws are in reverse chronological order, we can break early
                break
            
            if date_from <= fd_result_dt <= date_to:
                draws_in_range += 1
                print(f"Processing draw on {fd_result_dt.strftime('%d %b %Y')}...")
                
                # Extract prize numbers
                fd_result_first_prize = fd_result_soup.find_all(class_=FD_FIRST_PRIZE_CLASS)[0].get_text()
                fd_result_second_prize = fd_result_soup.find_all(class_=FD_SECOND_PRIZE_CLASS)[0].get_text()
                fd_result_third_prize = fd_result_soup.find_all(class_=FD_THIRD_PRIZE_CLASS)[0].get_text()
                
                fd_result_starter_prize_list = [
                    fd_prize_num.get_text() 
                    for fd_prize_num 
                    in fd_result_soup.select(FD_STARTER_PRIZE_CSS_SEL)
                ]
                
                fd_result_consolation_prize_list = [
                    fd_prize_num.get_text() 
                    for fd_prize_num 
                    in fd_result_soup.select(FD_CONSOLAION_PRIZE_CSS_SEL)
                ]
                
                # Add winning numbers to result list (all prize categories)
                fd_result_list.append([fd_result_dt, fd_result_first_prize, FD_FIRST_PRIZE_CLASS])
                fd_result_list.append([fd_result_dt, fd_result_second_prize, FD_SECOND_PRIZE_CLASS])
                fd_result_list.append([fd_result_dt, fd_result_third_prize, FD_THIRD_PRIZE_CLASS])
                
                for fd_prize_num in fd_result_starter_prize_list:
                    fd_result_list.append([fd_result_dt, fd_prize_num, FD_STARTER_PRIZE_CLASS])
                    
                for fd_prize_num in fd_result_consolation_prize_list:
                    fd_result_list.append([fd_result_dt, fd_prize_num, FD_CONSOLATION_PRIZE_CLASS])
            
            draws_processed += 1
            
        except Exception as e:
            print(f"Error processing draw {fd_sppl_id}: {e}")
            continue
    
    print(f"Processed {draws_processed} draws, found {draws_in_range} draws in the specified range\n")
    
    # Create DataFrame
    if not fd_result_list:
        print("No results found for the specified date range.")
        return pd.DataFrame(columns=['Date', 'Prize Number', 'Prize Type'])
    
    fd_result_df = pd.DataFrame(np.array(fd_result_list), columns=['Date', 'Prize Number', 'Prize Type'])
    fd_result_df.set_index('Date', inplace=True)
    
    return fd_result_df


def get_last_n_draws(df, n=6):
    """
    Get the last N draws from the DataFrame.
    
    Args:
        df: DataFrame with 4D results (indexed by Date)
        n: Number of draws to get (default: 6)
    
    Returns:
        pd.DataFrame: DataFrame with last N draws
    """
    if df.empty:
        return pd.DataFrame()
    
    # Get unique draw dates, sorted descending
    unique_dates = df.index.unique().sort_values(ascending=False)
    
    # Take the last N draws
    last_n_dates = unique_dates[:n]
    
    # Filter DataFrame to include only these dates
    last_n_draws_df = df[df.index.isin(last_n_dates)].copy()
    
    return last_n_draws_df


def analyze_first_digit_top3_prizes(last_6_draws_df):
    """
    Analyze the first digit occurrence in top 3 prizes (First, Second, Third) 
    for the last 6 draws.
    
    Args:
        last_6_draws_df: DataFrame with last 6 draws
    
    Returns:
        dict: Dictionary with first digit (0-9) as key and count as value
    """
    # Filter for top 3 prizes only
    top3_df = last_6_draws_df[
        last_6_draws_df['Prize Type'].isin([
            FD_FIRST_PRIZE_CLASS,
            FD_SECOND_PRIZE_CLASS,
            FD_THIRD_PRIZE_CLASS
        ])
    ]
    
    # Extract first digit from each prize number
    first_digits = []
    for prize_num in top3_df['Prize Number']:
        if len(str(prize_num)) >= 1:
            first_digit = str(prize_num).strip()[0]
            if first_digit.isdigit():
                first_digits.append(first_digit)
    
    # Count occurrences
    digit_counts = {}
    for digit in range(10):
        digit_counts[str(digit)] = first_digits.count(str(digit))
    
    return digit_counts


def analyze_first_digit_all_prizes(last_6_draws_df):
    """
    Analyze the first digit occurrence rate across all prize types 
    (First, Second, Third, Consolation, Starter) for the last 6 draws.
    
    Args:
        last_6_draws_df: DataFrame with last 6 draws
    
    Returns:
        dict: Dictionary with first digit (0-9) as key and count as value
    """
    # Extract first digit from each prize number
    first_digits = []
    for prize_num in last_6_draws_df['Prize Number']:
        if len(str(prize_num)) >= 1:
            first_digit = str(prize_num).strip()[0]
            if first_digit.isdigit():
                first_digits.append(first_digit)
    
    # Count occurrences
    digit_counts = {}
    for digit in range(10):
        digit_counts[str(digit)] = first_digits.count(str(digit))
    
    return digit_counts


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


def filter_generated_numbers(generated_numbers, past_6_months_df, past_1_year_df):
    """
    Filter generated numbers by removing those that:
    1. Appeared in any prize category in past 6 months
    2. Appeared in top 3 prizes (First, Second, Third) within one year
    3. Appeared more than once within one year
    
    Args:
        generated_numbers: Set of generated 4D numbers
        past_6_months_df: DataFrame with past 6 months data
        past_1_year_df: DataFrame with past 1 year data
    
    Returns:
        tuple: (filtered_numbers, appeared_in_6_months, appeared_in_top3_1year, appeared_multiple_1year)
    """
    print("=" * 60)
    print(f"Filtering {len(generated_numbers)} generated numbers")
    print("=" * 60)
    
    # Step 1: Filter out numbers that appeared in past 6 months (all prize categories)
    print("\nStep 1: Filtering by past 6 months (all prize categories)")
    winning_numbers_6_months = set(past_6_months_df['Prize Number'].unique())
    print(f"Total unique winning numbers in past 6 months: {len(winning_numbers_6_months)}")
    
    appeared_in_6_months = sorted([num for num in generated_numbers if num in winning_numbers_6_months])
    print(f"Generated numbers that appeared in past 6 months: {len(appeared_in_6_months)}")
    
    # First filter: remove numbers from past 6 months
    filtered_after_6_months = generated_numbers - winning_numbers_6_months
    print(f"Numbers remaining after 6-month filter: {len(filtered_after_6_months)}")
    
    # Step 2: Filter out numbers that appeared in top 3 prizes (First, Second, Third) in past 1 year
    print("\nStep 2: Filtering by top 3 prizes in past 1 year")
    if not past_1_year_df.empty:
        top_3_prizes_df = past_1_year_df[
            past_1_year_df['Prize Type'].isin([
                FD_FIRST_PRIZE_CLASS,
                FD_SECOND_PRIZE_CLASS,
                FD_THIRD_PRIZE_CLASS
            ])
        ]
        
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
        appeared_in_top3_1year = []
    
    # Step 3: Filter out numbers that appeared more than once in past 1 year
    print("\nStep 3: Filtering by multiple appearances in past 1 year")
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
        appeared_multiple_1year = []
    
    # Convert to sorted list for return
    filtered_numbers = sorted(filtered_numbers)
    
    return filtered_numbers, appeared_in_6_months, appeared_in_top3_1year, appeared_multiple_1year


def filter_all_4d_numbers(past_6_months_df, past_1_year_df):
    """
    Filter all 4D numbers (0000-9999), removing those that:
    1. Appeared in any prize category in past 6 months
    2. Appeared in top 3 prizes (First, Second, Third) within one year
    3. Appeared more than once within one year
    
    Args:
        past_6_months_df: DataFrame with past 6 months data (all prize categories)
        past_1_year_df: DataFrame with past 1 year data (all prize categories)
    
    Returns:
        tuple: (filtered_numbers, appeared_in_6_months, appeared_in_top3_1year, appeared_multiple_1year)
    """
    print("=" * 60)
    print("Filtering all 4D numbers (0000-9999)")
    print("=" * 60)
    
    # Generate all numbers in range 0000-9999
    all_4d_numbers = {str(num).zfill(4) for num in range(0, 10000)}
    print(f"Total numbers in range 0000-9999: {len(all_4d_numbers)}")
    
    # Step 1: Filter out numbers that appeared in past 6 months (all prize categories)
    print("\nStep 1: Filtering by past 6 months (all prize categories)")
    winning_numbers_6_months = set(past_6_months_df['Prize Number'].unique())
    print(f"Total unique winning numbers in past 6 months: {len(winning_numbers_6_months)}")
    
    appeared_in_6_months = sorted([num for num in all_4d_numbers if num in winning_numbers_6_months])
    print(f"Numbers that appeared in past 6 months: {len(appeared_in_6_months)}")
    
    # First filter: remove numbers from past 6 months
    filtered_after_6_months = all_4d_numbers - winning_numbers_6_months
    print(f"Numbers remaining after 6-month filter: {len(filtered_after_6_months)}")
    
    # Step 2: Filter out numbers that appeared in top 3 prizes (First, Second, Third) in past 1 year
    print("\nStep 2: Filtering by top 3 prizes in past 1 year")
    if not past_1_year_df.empty:
        top_3_prizes_df = past_1_year_df[
            past_1_year_df['Prize Type'].isin([
                FD_FIRST_PRIZE_CLASS,
                FD_SECOND_PRIZE_CLASS,
                FD_THIRD_PRIZE_CLASS
            ])
        ]
        
        top_3_numbers_1_year = set(top_3_prizes_df['Prize Number'].unique())
        print(f"Total unique top 3 prize numbers in past 1 year: {len(top_3_numbers_1_year)}")
        
        appeared_in_top3_1year = sorted([num for num in filtered_after_6_months if num in top_3_numbers_1_year])
        print(f"Numbers in filtered list that appeared in top 3 prizes (past 1 year): {len(appeared_in_top3_1year)}")
        
        # Second filter: remove top 3 prize numbers from past 1 year
        filtered_after_top3 = filtered_after_6_months - top_3_numbers_1_year
        print(f"Numbers remaining after top 3 filter: {len(filtered_after_top3)}")
    else:
        print("No past 1 year data available, skipping top 3 filter")
        filtered_after_top3 = filtered_after_6_months
        appeared_in_top3_1year = []
    
    # Step 3: Filter out numbers that appeared more than once in past 1 year
    print("\nStep 3: Filtering by multiple appearances in past 1 year")
    if not past_1_year_df.empty:
        # Count occurrences of each number in past 1 year
        number_counts = past_1_year_df['Prize Number'].value_counts()
        numbers_appeared_multiple = set(number_counts[number_counts > 1].index)
        print(f"Total numbers that appeared more than once in past 1 year: {len(numbers_appeared_multiple)}")
        
        appeared_multiple_1year = sorted([num for num in filtered_after_top3 if num in numbers_appeared_multiple])
        print(f"Numbers in filtered list that appeared multiple times (past 1 year): {len(appeared_multiple_1year)}")
        
        # Third filter: remove numbers that appeared multiple times
        filtered_numbers = filtered_after_top3 - numbers_appeared_multiple
        print(f"Final filtered numbers: {len(filtered_numbers)}")
    else:
        print("No past 1 year data available, skipping multiple appearances filter")
        filtered_numbers = filtered_after_top3
        appeared_multiple_1year = []
    
    # Convert to sorted list for return
    filtered_numbers = sorted(filtered_numbers)
    
    return filtered_numbers, appeared_in_6_months, appeared_in_top3_1year, appeared_multiple_1year


def main():
    """Main function to filter 4D numbers based on first digit analysis."""
    print("=" * 60)
    print("Filter 4D Numbers: Based on First Digit Analysis")
    print("=" * 60)
    
    today = datetime.now()
    six_months_ago = today - timedelta(days=180)
    one_year_ago = today - timedelta(days=365)
    
    # Fetch past 6 months data (with caching) - needed for last 6 draws and filtering
    print("\nFetching past 6 months of 4D results (all prize categories)...")
    past_6_months_df = fetch_fd_results_with_cache(
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
    top3_first_digit_counts = analyze_first_digit_top3_prizes(last_6_draws_df)
    print("First digit occurrence in top 3 prizes (past 6 draws):")
    for digit in sorted(top3_first_digit_counts.keys()):
        print(f"  Digit {digit}: {top3_first_digit_counts[digit]} occurrences")
    
    # Select digits with 0 occurrence in top 3 prizes (priority), otherwise use low occurrence threshold
    zero_occurrence_digits = [digit for digit, count in top3_first_digit_counts.items() if count == 0]
    selected_digits_step1 = select_digits_priority_zero(top3_first_digit_counts)
    if zero_occurrence_digits:
        print(f"\nSelected first digits from top 3 analysis (0 occurrence): {selected_digits_step1}")
    else:
        print(f"\nSelected first digits from top 3 analysis (low occurrence): {selected_digits_step1}")
    
    # Step 3: Analyze first digit occurrence across all prize types in last 6 draws
    print("\n" + "=" * 60)
    print("Step 3: Analyzing first digit occurrence across all prize types (past 6 draws)")
    print("=" * 60)
    all_prizes_first_digit_counts = analyze_first_digit_all_prizes(last_6_draws_df)
    print("First digit occurrence across all prize types (past 6 draws):")
    for digit in sorted(all_prizes_first_digit_counts.keys()):
        print(f"  Digit {digit}: {all_prizes_first_digit_counts[digit]} occurrences")
    
    # Select digit(s) with the lowest occurrence rate across all prizes
    selected_digits_step2 = select_digits_lowest_occurrence(all_prizes_first_digit_counts)
    min_occurrence = min(all_prizes_first_digit_counts.values()) if all_prizes_first_digit_counts else 0
    print(f"\nSelected first digit(s) from all prizes analysis (lowest occurrence: {min_occurrence}): {selected_digits_step2}")
    
    # Combine selections: keep digits that are in either list (union)
    # This combines digits from both top 3 prizes analysis and all prizes analysis
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
    past_1_year_df = fetch_fd_results_with_cache(
        one_year_ago, 
        today, 
        CACHE_1YEAR_FILE, 
        cache_label="1 year data"
    )
    
    if past_1_year_df.empty:
        print("Warning: No data found for past 1 year. Will only filter by 6 months data.")
        past_1_year_df = pd.DataFrame(columns=['Date', 'Prize Number', 'Prize Type'])
    
    # Step 5: Filter generated numbers
    filtered_numbers, appeared_in_6_months, appeared_in_top3_1year, appeared_multiple_1year = filter_generated_numbers(
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
    
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Save to file
    output_file = os.path.join(OUTPUT_DIR, f"filtered_first_digit_{today.strftime('%Y%m%d')}.txt")
    with open(output_file, 'w') as f:
        f.write("Filtered 4D Numbers: Based on First Digit Analysis\n")
        f.write("=" * 60 + "\n")
        f.write(f"Generated on: {today.strftime('%d %b %Y %H:%M:%S')}\n")
        f.write(f"Last 6 draws analyzed:\n")
        for date in unique_dates:
            f.write(f"  - {date.strftime('%d %b %Y')}\n")
        f.write(f"Selected first digits: {', '.join(final_selected_digits)}\n")
        f.write(f"Date range for filtering (6 months): {six_months_ago.strftime('%d %b %Y')} to {today.strftime('%d %b %Y')}\n")
        f.write(f"Date range for filtering (1 year): {one_year_ago.strftime('%d %b %Y')} to {today.strftime('%d %b %Y')}\n")
        f.write(f"Total generated numbers: {len(generated_numbers)}\n")
        f.write(f"Numbers appeared in past 6 months (all prizes): {len(appeared_in_6_months)}\n")
        f.write(f"Numbers appeared in top 3 prizes (past 1 year): {len(appeared_in_top3_1year)}\n")
        f.write(f"Numbers appeared multiple times (past 1 year): {len(appeared_multiple_1year)}\n")
        f.write(f"Final filtered numbers: {len(filtered_numbers)}\n")
        f.write("=" * 60 + "\n\n")
        
        # Write numbers in groups of 10
        for i in range(0, len(filtered_numbers), 10):
            group = filtered_numbers[i:i+10]
            f.write("  ".join(group) + "\n")
    
    print(f"\nResults saved to: {output_file}")
    
    # Also save as CSV
    csv_output = os.path.join(OUTPUT_DIR, f"filtered_first_digit_{today.strftime('%Y%m%d')}.csv")
    result_df = pd.DataFrame({
        'Number': filtered_numbers
    })
    result_df.to_csv(csv_output, index=False)
    print(f"Results also saved to: {csv_output}")
    
    # Save appeared numbers for reference
    if appeared_in_6_months:
        appeared_file = os.path.join(OUTPUT_DIR, f"appeared_first_digit_6months_{today.strftime('%Y%m%d')}.csv")
        appeared_df = pd.DataFrame({
            'Number': appeared_in_6_months
        })
        appeared_df.to_csv(appeared_file, index=False)
        print(f"6-month appeared numbers saved to: {appeared_file}")
    
    if appeared_in_top3_1year:
        appeared_file = os.path.join(OUTPUT_DIR, f"appeared_first_digit_top3_1year_{today.strftime('%Y%m%d')}.csv")
        appeared_df = pd.DataFrame({
            'Number': appeared_in_top3_1year
        })
        appeared_df.to_csv(appeared_file, index=False)
        print(f"Top 3 prize appeared numbers (1 year) saved to: {appeared_file}")
    
    if appeared_multiple_1year:
        appeared_file = os.path.join(OUTPUT_DIR, f"appeared_first_digit_multiple_1year_{today.strftime('%Y%m%d')}.csv")
        appeared_df = pd.DataFrame({
            'Number': appeared_multiple_1year
        })
        appeared_df.to_csv(appeared_file, index=False)
        print(f"Multiple appearance numbers (1 year) saved to: {appeared_file}")
    
    # Display sample
    print("\n" + "=" * 60)
    print("Sample of filtered numbers (first 20):")
    print("=" * 60)
    for i in range(0, min(20, len(filtered_numbers)), 10):
        group = filtered_numbers[i:i+10]
        print("  ".join(group))
    
    return filtered_numbers


if __name__ == "__main__":
    results = main()

