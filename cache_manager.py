"""
Cache management module for storing and retrieving 4D lottery results.
Handles pickle-based caching with date tracking.
"""

import pickle
import os
from datetime import datetime, timedelta
import pandas as pd
from data_fetcher import fetch_fd_results


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


def fetch_with_cache(date_from, date_to, cache_file, cache_label=""):
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

