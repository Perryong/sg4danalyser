"""
Constants used across the 4D analyzer modules.
Centralizes all configuration values.
"""

# Prize type constants
FD_FIRST_PRIZE_CLASS = 'tdFirstPrize'
FD_SECOND_PRIZE_CLASS = 'tdSecondPrize'
FD_THIRD_PRIZE_CLASS = 'tdThirdPrize'
FD_STARTER_PRIZE_CLASS = 'tbodyStarterPrizes'
FD_CONSOLATION_PRIZE_CLASS = 'tbodyConsolationPrizes'

# Directory constants
import os
CACHE_DIR = 'cache'
OUTPUT_DIR = 'output'

# Cache file paths (using os.path.join for cross-platform compatibility)
CACHE_6MONTHS_FILE = os.path.join(CACHE_DIR, 'fd_results_6months.pkl')
CACHE_1YEAR_FILE = os.path.join(CACHE_DIR, 'fd_results_1year.pkl')

# Default prize weights for weighted analysis
DEFAULT_PRIZE_WEIGHTS = {
    FD_FIRST_PRIZE_CLASS: 1.0,
    FD_SECOND_PRIZE_CLASS: 1.0,
    FD_THIRD_PRIZE_CLASS: 1.0,
    FD_STARTER_PRIZE_CLASS: 0.3,
    FD_CONSOLATION_PRIZE_CLASS: 0.3
}

# Top 3 prize types (for filtering)
TOP_3_PRIZE_TYPES = [
    FD_FIRST_PRIZE_CLASS,
    FD_SECOND_PRIZE_CLASS,
    FD_THIRD_PRIZE_CLASS
]

