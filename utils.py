"""
Utility functions for 4D analyzer.
Common helper functions used across modules.
"""

import pandas as pd
import os


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


def save_results_to_file(filtered_numbers, output_dir, filename_prefix, metadata=None):
    """
    Save filtered numbers to text and CSV files.
    
    Args:
        filtered_numbers: List of filtered 4D numbers
        output_dir: Output directory
        filename_prefix: Prefix for output files (e.g., 'filtered_improved')
        metadata: Optional dictionary with metadata to include in text file
    
    Returns:
        tuple: (text_file_path, csv_file_path)
    """
    os.makedirs(output_dir, exist_ok=True)
    today = pd.Timestamp.now()
    
    # Save as text file
    text_file = os.path.join(output_dir, f"{filename_prefix}_{today.strftime('%Y%m%d')}.txt")
    with open(text_file, 'w') as f:
        if metadata:
            for key, value in metadata.items():
                f.write(f"{key}: {value}\n")
            f.write("=" * 80 + "\n\n")
        
        # Write numbers in groups of 10
        for i in range(0, len(filtered_numbers), 10):
            group = filtered_numbers[i:i+10]
            f.write("  ".join(group) + "\n")
    
    # Save as CSV
    csv_file = os.path.join(output_dir, f"{filename_prefix}_{today.strftime('%Y%m%d')}.csv")
    result_df = pd.DataFrame({'Number': filtered_numbers})
    result_df.to_csv(csv_file, index=False)
    
    return text_file, csv_file

