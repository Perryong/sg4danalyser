"""
Simulate winning amounts if buying all numbers in the filtered list.

Calculates:
- Total cost (buying all numbers)
- Maximum winning scenario (Top 3 prizes + 10 starters + 10 consolations)
- Minimum winning scenario (0 prizes - worst case)
- Net profit/loss
"""

import pandas as pd
import os
import glob
from datetime import datetime

# Prize amounts based on Singapore Pools 4D prize structure
# Values are for "1 big" bet type
PRIZE_AMOUNTS = {
    'FIRST': 2000,      # 1 big
    'SECOND': 1000,     # 1 big
    'THIRD': 400,       # 1 big
    'STARTER': 250,     # 1 big
    'CONSOLATION': 60   # 1 big
}

# Cost per 4D number (standard bet)
COST_PER_NUMBER = 1.0

# Output directory for results
OUTPUT_DIR = 'output'


def find_latest_filtered_file(pattern='filtered_first_digit_*.csv'):
    """
    Find the latest filtered numbers CSV file matching the pattern.
    Searches in the output directory first, then current directory.
    
    Args:
        pattern: File pattern to search for (default: 'filtered_first_digit_*.csv')
    
    Returns:
        str: Path to the latest file, or None if not found
    """
    # Search in output directory first
    output_pattern = os.path.join(OUTPUT_DIR, pattern)
    files = glob.glob(output_pattern)
    
    # Also search in current directory (for backward compatibility)
    if not files:
        files = glob.glob(pattern)
    
    if not files:
        return None
    
    # Sort by modification time (newest first)
    latest_file = max(files, key=os.path.getmtime)
    return latest_file


def load_filtered_numbers(csv_file):
    """Load filtered numbers from CSV file."""
    df = pd.read_csv(csv_file)
    numbers = df['Number'].astype(str).str.zfill(4).tolist()
    return numbers


def calculate_winning_scenario(filtered_numbers, first_prize=0, second_prize=0, third_prize=0, num_starters=0, num_consolations=0):
    """
    Calculate winning scenario for a specific combination of prizes.
    
    Args:
        filtered_numbers: List of filtered 4D numbers
        first_prize: Number of first prizes (0 or 1)
        second_prize: Number of second prizes (0 or 1)
        third_prize: Number of third prizes (0 or 1)
        num_starters: Number of starter prizes (0-10)
        num_consolations: Number of consolation prizes (0-10)
    
    Returns:
        dict: Dictionary containing cost, winnings breakdown, and totals
    """
    total_numbers = len(filtered_numbers)
    total_cost = total_numbers * COST_PER_NUMBER
    
    first_prize_amount = first_prize * PRIZE_AMOUNTS['FIRST']
    second_prize_amount = second_prize * PRIZE_AMOUNTS['SECOND']
    third_prize_amount = third_prize * PRIZE_AMOUNTS['THIRD']
    starters_total = num_starters * PRIZE_AMOUNTS['STARTER']
    consolations_total = num_consolations * PRIZE_AMOUNTS['CONSOLATION']
    
    total_winnings = first_prize_amount + second_prize_amount + third_prize_amount + starters_total + consolations_total
    net_profit = total_winnings - total_cost
    
    return {
        'total_numbers': total_numbers,
        'total_cost': total_cost,
        'winnings': {
            'first_prize': first_prize_amount,
            'second_prize': second_prize_amount,
            'third_prize': third_prize_amount,
            'starters': {
                'count': num_starters,
                'amount_per_prize': PRIZE_AMOUNTS['STARTER'],
                'total': starters_total
            },
            'consolations': {
                'count': num_consolations,
                'amount_per_prize': PRIZE_AMOUNTS['CONSOLATION'],
                'total': consolations_total
            },
            'total': total_winnings
        },
        'net_profit': net_profit,
        'roi_percent': (net_profit / total_cost * 100) if total_cost > 0 else 0,
        'scenario': {
            'first_prize': first_prize,
            'second_prize': second_prize,
            'third_prize': third_prize,
            'starters': num_starters,
            'consolations': num_consolations
        }
    }


def generate_all_scenarios(filtered_numbers, max_starters=10, max_consolations=10):
    """
    Generate all possible winning scenarios.
    
    Args:
        filtered_numbers: List of filtered 4D numbers
        max_starters: Maximum number of starter prizes to consider (default: 10)
        max_consolations: Maximum number of consolation prizes to consider (default: 10)
    
    Returns:
        list: List of scenario result dictionaries
    """
    scenarios = []
    
    # Generate all combinations
    # Top 3 prizes: 0 or 1 each (2^3 = 8 combinations)
    # Starters: 0 to max_starters
    # Consolations: 0 to max_consolations
    
    for first in [0, 1]:
        for second in [0, 1]:
            for third in [0, 1]:
                for starters in range(max_starters + 1):
                    for consolations in range(max_consolations + 1):
                        scenario = calculate_winning_scenario(
                            filtered_numbers,
                            first_prize=first,
                            second_prize=second,
                            third_prize=third,
                            num_starters=starters,
                            num_consolations=consolations
                        )
                        scenarios.append(scenario)
    
    return scenarios


def generate_top3_only_scenarios(filtered_numbers):
    """
    Generate scenarios with only top 3 prizes (no starters or consolations).
    This gives 8 combinations: all permutations of winning 0 or 1 of each top 3 prize.
    
    Args:
        filtered_numbers: List of filtered 4D numbers
    
    Returns:
        list: List of scenario result dictionaries
    """
    scenarios = []
    
    for first in [0, 1]:
        for second in [0, 1]:
            for third in [0, 1]:
                scenario = calculate_winning_scenario(
                    filtered_numbers,
                    first_prize=first,
                    second_prize=second,
                    third_prize=third,
                    num_starters=0,
                    num_consolations=0
                )
                scenarios.append(scenario)
    
    return scenarios


def generate_complete_scenarios(filtered_numbers, max_starters=10, max_consolations=10):
    """
    Generate complete scenarios with all combinations of prizes.
    This gives 2 (First) × 2 (Second) × 2 (Third) × 11 (Starters: 0-10) × 11 (Consolations: 0-10) = 968 scenarios.
    
    Args:
        filtered_numbers: List of filtered 4D numbers
        max_starters: Maximum number of starter prizes (default: 10)
        max_consolations: Maximum number of consolation prizes (default: 10)
    
    Returns:
        list: List of scenario result dictionaries
    """
    scenarios = []
    
    # First ∈ {0,1} (2 options)
    # Second ∈ {0,1} (2 options)
    # Third ∈ {0,1} (2 options)
    # Starter ∈ {0,1,2,...,10} (11 options)
    # Consolation ∈ {0,1,2,...,10} (11 options)
    # Total: 2 × 2 × 2 × 11 × 11 = 968 scenarios
    
    print(f"Generating all {2 * 2 * 2 * (max_starters + 1) * (max_consolations + 1)} scenarios...")
    
    for first in [0, 1]:
        for second in [0, 1]:
            for third in [0, 1]:
                for starters in range(max_starters + 1):
                    for consolations in range(max_consolations + 1):
                        scenario = calculate_winning_scenario(
                            filtered_numbers,
                            first_prize=first,
                            second_prize=second,
                            third_prize=third,
                            num_starters=starters,
                            num_consolations=consolations
                        )
                        scenarios.append(scenario)
    
    return scenarios


def print_scenario_summary(scenarios):
    """
    Print summary of all scenarios.
    
    Args:
        scenarios: List of scenario result dictionaries
    """
    print("=" * 100)
    print("ALL WINNING SCENARIO PERMUTATIONS")
    print("=" * 100)
    print()
    print(f"{'#':<5} {'1st':<5} {'2nd':<5} {'3rd':<5} {'Start':<7} {'Consol':<7} {'Winnings':<12} {'Cost':<12} {'Net Profit':<15} {'ROI %':<10}")
    print("-" * 100)
    
    for idx, scenario in enumerate(scenarios, 1):
        s = scenario['scenario']
        print(f"{idx:<5} {s['first_prize']:<5} {s['second_prize']:<5} {s['third_prize']:<5} "
              f"{s['starters']:<7} {s['consolations']:<7} "
              f"${scenario['winnings']['total']:>10,.2f} "
              f"${scenario['total_cost']:>10,.2f} "
              f"${scenario['net_profit']:>13,.2f} "
              f"{scenario['roi_percent']:>8.2f}%")


def save_scenarios_to_file(scenarios, csv_file, output_file):
    """
    Save all scenarios to file.
    
    Args:
        scenarios: List of scenario result dictionaries
        csv_file: Input CSV file name
        output_file: Output file path
    """
    with open(output_file, 'w') as f:
        f.write("=" * 100 + "\n")
        f.write("ALL WINNING SCENARIO PERMUTATIONS\n")
        f.write("=" * 100 + "\n\n")
        
        f.write(f"Date: {datetime.now().strftime('%d %b %Y %H:%M:%S')}\n")
        f.write(f"Input File: {csv_file}\n")
        f.write(f"Total Scenarios: {len(scenarios)}\n\n")
        
        f.write("-" * 100 + "\n")
        f.write(f"{'#':<5} {'1st':<5} {'2nd':<5} {'3rd':<5} {'Start':<7} {'Consol':<7} {'Winnings':<12} {'Cost':<12} {'Net Profit':<15} {'ROI %':<10}\n")
        f.write("-" * 100 + "\n")
        
        for idx, scenario in enumerate(scenarios, 1):
            s = scenario['scenario']
            f.write(f"{idx:<5} {s['first_prize']:<5} {s['second_prize']:<5} {s['third_prize']:<5} "
                   f"{s['starters']:<7} {s['consolations']:<7} "
                   f"${scenario['winnings']['total']:>10,.2f} "
                   f"${scenario['total_cost']:>10,.2f} "
                   f"${scenario['net_profit']:>13,.2f} "
                   f"{scenario['roi_percent']:>8.2f}%\n")
        
        f.write("=" * 100 + "\n")


def calculate_min_winnings(filtered_numbers):
    """
    Calculate minimum winning scenario (worst case - no prizes).
    
    Args:
        filtered_numbers: List of filtered 4D numbers
    
    Returns:
        dict: Dictionary containing cost, winnings breakdown, and totals
    """
    total_numbers = len(filtered_numbers)
    
    # Calculate total cost
    total_cost = total_numbers * COST_PER_NUMBER
    
    # Minimum winning scenario (worst case):
    # - 0 First Prize
    # - 0 Second Prize
    # - 0 Third Prize
    # - 0 Starter Prizes
    # - 0 Consolation Prizes
    
    total_winnings = 0
    net_profit = total_winnings - total_cost
    
    return {
        'total_numbers': total_numbers,
        'total_cost': total_cost,
        'winnings': {
            'first_prize': 0,
            'second_prize': 0,
            'third_prize': 0,
            'starters': {
                'count': 0,
                'amount_per_prize': PRIZE_AMOUNTS['STARTER'],
                'total': 0
            },
            'consolations': {
                'count': 0,
                'amount_per_prize': PRIZE_AMOUNTS['CONSOLATION'],
                'total': 0
            },
            'total': total_winnings
        },
        'net_profit': net_profit,
        'roi_percent': (net_profit / total_cost * 100) if total_cost > 0 else 0
    }


def calculate_max_winnings(filtered_numbers, num_starters=10, num_consolations=10):
    """
    Calculate maximum winning scenario.
    
    Args:
        filtered_numbers: List of filtered 4D numbers
        num_starters: Number of starter prizes (default: 10)
        num_consolations: Number of consolation prizes (default: 10)
    
    Returns:
        dict: Dictionary containing cost, winnings breakdown, and totals
    """
    total_numbers = len(filtered_numbers)
    
    # Calculate total cost
    total_cost = total_numbers * COST_PER_NUMBER
    
    # Maximum winning scenario:
    # - 1 First Prize
    # - 1 Second Prize
    # - 1 Third Prize
    # - num_starters Starter Prizes
    # - num_consolations Consolation Prizes
    
    first_prize = PRIZE_AMOUNTS['FIRST']
    second_prize = PRIZE_AMOUNTS['SECOND']
    third_prize = PRIZE_AMOUNTS['THIRD']
    starter_prize = PRIZE_AMOUNTS['STARTER']
    consolation_prize = PRIZE_AMOUNTS['CONSOLATION']
    
    starters_total = num_starters * starter_prize
    consolations_total = num_consolations * consolation_prize
    
    total_winnings = first_prize + second_prize + third_prize + starters_total + consolations_total
    net_profit = total_winnings - total_cost
    
    return {
        'total_numbers': total_numbers,
        'total_cost': total_cost,
        'winnings': {
            'first_prize': first_prize,
            'second_prize': second_prize,
            'third_prize': third_prize,
            'starters': {
                'count': num_starters,
                'amount_per_prize': starter_prize,
                'total': starters_total
            },
            'consolations': {
                'count': num_consolations,
                'amount_per_prize': consolation_prize,
                'total': consolations_total
            },
            'total': total_winnings
        },
        'net_profit': net_profit,
        'roi_percent': (net_profit / total_cost * 100) if total_cost > 0 else 0
    }


def print_results(results, scenario_type="MAXIMUM"):
    """Print formatted results."""
    print("=" * 70)
    print(f"4D WINNING SIMULATION - {scenario_type} WINNING SCENARIO")
    print("=" * 70)
    print()
    
    print(f"Total Numbers in Filtered List: {results['total_numbers']:,}")
    print(f"Cost per Number: ${COST_PER_NUMBER:.2f}")
    print(f"Total Cost: ${results['total_cost']:,.2f}")
    print()
    
    print("-" * 70)
    print(f"PRIZE BREAKDOWN ({scenario_type.title()} Winning Scenario):")
    print("-" * 70)
    print(f"  First Prize (1 big):       ${results['winnings']['first_prize']:,}")
    print(f"  Second Prize (1 big):      ${results['winnings']['second_prize']:,}")
    print(f"  Third Prize (1 big):       ${results['winnings']['third_prize']:,}")
    print()
    
    starters = results['winnings']['starters']
    print(f"  Starter Prizes:")
    print(f"    - Count: {starters['count']}")
    print(f"    - Amount per prize: ${starters['amount_per_prize']:,}")
    print(f"    - Subtotal: ${starters['total']:,}")
    print()
    
    consolations = results['winnings']['consolations']
    print(f"  Consolation Prizes:")
    print(f"    - Count: {consolations['count']}")
    print(f"    - Amount per prize: ${consolations['amount_per_prize']:,}")
    print(f"    - Subtotal: ${consolations['total']:,}")
    print()
    
    print("-" * 70)
    print(f"TOTAL WINNINGS: ${results['winnings']['total']:,}")
    print(f"NET PROFIT: ${results['net_profit']:,.2f}")
    print(f"ROI: {results['roi_percent']:.2f}%")
    print("=" * 70)


def save_results_to_file(results, csv_file, output_file, scenario_type="MAXIMUM"):
    """Save results to file."""
    with open(output_file, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write(f"4D WINNING SIMULATION - {scenario_type} WINNING SCENARIO\n")
        f.write("=" * 70 + "\n\n")
        
        f.write(f"Date: {datetime.now().strftime('%d %b %Y %H:%M:%S')}\n")
        f.write(f"Input File: {csv_file}\n\n")
        
        f.write(f"Total Numbers in Filtered List: {results['total_numbers']:,}\n")
        f.write(f"Cost per Number: ${COST_PER_NUMBER:.2f}\n")
        f.write(f"Total Cost: ${results['total_cost']:,.2f}\n\n")
        
        f.write("-" * 70 + "\n")
        f.write(f"PRIZE BREAKDOWN ({scenario_type.title()} Winning Scenario):\n")
        f.write("-" * 70 + "\n")
        f.write(f"  First Prize (1 big):       ${results['winnings']['first_prize']:,}\n")
        f.write(f"  Second Prize (1 big):      ${results['winnings']['second_prize']:,}\n")
        f.write(f"  Third Prize (1 big):       ${results['winnings']['third_prize']:,}\n\n")
        
        starters = results['winnings']['starters']
        f.write(f"  Starter Prizes:\n")
        f.write(f"    - Count: {starters['count']}\n")
        f.write(f"    - Amount per prize: ${starters['amount_per_prize']:,}\n")
        f.write(f"    - Subtotal: ${starters['total']:,}\n\n")
        
        consolations = results['winnings']['consolations']
        f.write(f"  Consolation Prizes:\n")
        f.write(f"    - Count: {consolations['count']}\n")
        f.write(f"    - Amount per prize: ${consolations['amount_per_prize']:,}\n")
        f.write(f"    - Subtotal: ${consolations['total']:,}\n\n")
        
        f.write("-" * 70 + "\n")
        f.write(f"TOTAL WINNINGS: ${results['winnings']['total']:,}\n")
        f.write(f"NET PROFIT: ${results['net_profit']:,.2f}\n")
        f.write(f"ROI: {results['roi_percent']:.2f}%\n")
        f.write("=" * 70 + "\n")


def main():
    """Main function."""
    # Automatically find the latest filtered numbers CSV file
    csv_file = find_latest_filtered_file()
    
    if csv_file is None:
        print("Error: No filtered numbers CSV file found.")
        print("Please run 4D_analyzer.py first to generate filtered numbers.")
        return
    
    print(f"Auto-detected filtered numbers file: {csv_file}")
    
    try:
        filtered_numbers = load_filtered_numbers(csv_file)
        print(f"Loaded {len(filtered_numbers)} filtered numbers from {csv_file}")
        print()
    except FileNotFoundError:
        print(f"Error: File '{csv_file}' not found.")
        return
    except Exception as e:
        print(f"Error loading file: {e}")
        return
    
    # Generate complete scenarios (2×2×2×11×11 = 968 scenarios)
    print("Generating complete scenarios (all permutations)...")
    print("First ∈ {0,1}, Second ∈ {0,1}, Third ∈ {0,1}, Starter ∈ {0,1,...,10}, Consolation ∈ {0,1,...,10}")
    scenarios = generate_complete_scenarios(filtered_numbers, max_starters=10, max_consolations=10)
    print(f"Generated {len(scenarios)} scenarios\n")
    
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Print summary of all scenarios
    print_scenario_summary(scenarios)
    
    # Save scenarios to file
    output_file = os.path.join(OUTPUT_DIR, f"simulation_all_scenarios_{datetime.now().strftime('%Y%m%d')}.txt")
    save_scenarios_to_file(scenarios, csv_file, output_file)
    
    print(f"\n\nResults saved to: {output_file}")
    
    # Also save as CSV for easier analysis
    csv_output = os.path.join(OUTPUT_DIR, f"simulation_all_scenarios_{datetime.now().strftime('%Y%m%d')}.csv")
    scenarios_data = []
    for idx, scenario in enumerate(scenarios, 1):
        s = scenario['scenario']
        scenarios_data.append({
            'Scenario': idx,
            'First_Prize': s['first_prize'],
            'Second_Prize': s['second_prize'],
            'Third_Prize': s['third_prize'],
            'Starters': s['starters'],
            'Consolations': s['consolations'],
            'Total_Winnings': scenario['winnings']['total'],
            'Total_Cost': scenario['total_cost'],
            'Net_Profit': scenario['net_profit'],
            'ROI_Percent': scenario['roi_percent']
        })
    
    df = pd.DataFrame(scenarios_data)
    df.to_csv(csv_output, index=False)
    print(f"CSV results saved to: {csv_output}")


if __name__ == "__main__":
    main()

