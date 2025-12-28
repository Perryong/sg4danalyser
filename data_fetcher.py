"""
Data fetching module for Singapore 4D lottery results.
Handles web scraping and data retrieval from Singapore Pools website.
"""

from datetime import datetime
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from constants import (
    FD_FIRST_PRIZE_CLASS, FD_SECOND_PRIZE_CLASS, FD_THIRD_PRIZE_CLASS,
    FD_STARTER_PRIZE_CLASS, FD_CONSOLATION_PRIZE_CLASS
)

# URL Constants
FD_DRAW_LIST_URL = 'http://www.singaporepools.com.sg/DataFileArchive/Lottery/Output/fourd_result_draw_list_en.html'
FD_RESULT_URL = 'http://www.singaporepools.com.sg/en/product/Pages/4d_results.aspx?sppl='

# HTML Parsing Constants
PARSER_NAME = 'html.parser'
SPPL_ATTR = 'querystring'
SPPL_TAG = 'option'
DT_FORMAT = '%d %b %Y'
DRAW_DATE_CLASS = 'drawDate'

FD_STARTER_PRIZE_CSS_SEL = ' '.join(['.' + FD_STARTER_PRIZE_CLASS, 'td'])
FD_CONSOLAION_PRIZE_CSS_SEL = ' '.join(['.' + FD_CONSOLATION_PRIZE_CLASS, 'td'])


def fetch_fd_results(date_from, date_to):
    """
    Fetch 4D results for a specified date range.
    
    Args:
        date_from: Start date (datetime)
        date_to: End date (datetime)
    
    Returns:
        pd.DataFrame: DataFrame containing 4D results with columns:
            - Index: Date (DatetimeIndex)
            - Prize Number: str
            - Prize Type: str
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

