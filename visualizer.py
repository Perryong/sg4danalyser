"""
Visualization module for 4D lottery analysis.
Generates matplotlib charts for various analysis results.
"""

import matplotlib.pyplot as plt
import numpy as np
import os
from datetime import datetime


def visualize_weighted_digit_counts(window_analyses, output_dir='output'):
    """
    Visualize weighted digit counts across different window sizes.
    
    Args:
        window_analyses: Dictionary with window_size as key and analysis results as value
        output_dir: Directory to save the plot
    """
    fig, axes = plt.subplots(len(window_analyses), 1, figsize=(12, 4 * len(window_analyses)))
    if len(window_analyses) == 1:
        axes = [axes]
    
    for idx, (window_size, analysis) in enumerate(sorted(window_analyses.items())):
        weighted_counts = analysis['weighted_counts']
        digits = sorted(weighted_counts.keys())
        counts = [weighted_counts[d] for d in digits]
        
        axes[idx].bar(digits, counts, color='steelblue', alpha=0.7)
        axes[idx].set_title(f'Weighted Digit Counts (Window: {window_size} draws)', fontsize=12, fontweight='bold')
        axes[idx].set_xlabel('First Digit', fontsize=10)
        axes[idx].set_ylabel('Weighted Count', fontsize=10)
        axes[idx].grid(axis='y', alpha=0.3)
        axes[idx].set_xticks(digits)
        
        # Add value labels on bars
        for i, (d, c) in enumerate(zip(digits, counts)):
            axes[idx].text(i, c, f'{c:.2f}', ha='center', va='bottom', fontsize=8)
    
    plt.tight_layout()
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f'weighted_digit_counts_{datetime.now().strftime("%Y%m%d")}.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved weighted digit counts visualization to: {output_file}")


def visualize_bayesian_probabilities(window_analyses, output_dir='output'):
    """
    Visualize Bayesian-smoothed probabilities across different window sizes.
    
    Args:
        window_analyses: Dictionary with window_size as key and analysis results as value
        output_dir: Directory to save the plot
    """
    fig, axes = plt.subplots(len(window_analyses), 1, figsize=(12, 4 * len(window_analyses)))
    if len(window_analyses) == 1:
        axes = [axes]
    
    for idx, (window_size, analysis) in enumerate(sorted(window_analyses.items())):
        probabilities = analysis['probabilities']
        digits = sorted(probabilities.keys())
        probs = [probabilities[d] for d in digits]
        
        colors = ['green' if p > 0.1 else 'orange' if p > 0.05 else 'red' for p in probs]
        axes[idx].bar(digits, probs, color=colors, alpha=0.7)
        axes[idx].axhline(y=0.1, color='gray', linestyle='--', alpha=0.5, label='Uniform (10%)')
        axes[idx].set_title(f'Bayesian-Smoothed Probabilities (Window: {window_size} draws)', fontsize=12, fontweight='bold')
        axes[idx].set_xlabel('First Digit', fontsize=10)
        axes[idx].set_ylabel('Probability', fontsize=10)
        axes[idx].grid(axis='y', alpha=0.3)
        axes[idx].set_xticks(digits)
        axes[idx].legend()
        
        # Add value labels on bars
        for i, (d, p) in enumerate(zip(digits, probs)):
            axes[idx].text(i, p, f'{p:.3f}', ha='center', va='bottom', fontsize=8)
    
    plt.tight_layout()
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f'bayesian_probabilities_{datetime.now().strftime("%Y%m%d")}.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved Bayesian probabilities visualization to: {output_file}")


def visualize_chi_square_tests(window_analyses, output_dir='output'):
    """
    Visualize chi-square test results across different window sizes.
    
    Args:
        window_analyses: Dictionary with window_size as key and analysis results as value
        output_dir: Directory to save the plot
    """
    window_sizes = []
    chi2_stats = []
    pvalues = []
    is_uniform = []
    
    for window_size, analysis in sorted(window_analyses.items()):
        chi2_result = analysis['chi2_result']
        window_sizes.append(window_size)
        chi2_stats.append(chi2_result['chi2'])
        pvalues.append(chi2_result['pvalue'])
        is_uniform.append(chi2_result['is_uniform'])
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Chi-square statistics
    colors = ['red' if not u else 'green' for u in is_uniform]
    ax1.bar([str(ws) for ws in window_sizes], chi2_stats, color=colors, alpha=0.7)
    ax1.set_title('Chi-Square Test Statistics', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Window Size (draws)', fontsize=10)
    ax1.set_ylabel('Chi-Square Statistic', fontsize=10)
    ax1.grid(axis='y', alpha=0.3)
    ax1.axhline(y=16.92, color='red', linestyle='--', alpha=0.5, label='Critical Value (α=0.05, df=9)')
    ax1.legend()
    
    # P-values
    ax2.bar([str(ws) for ws in window_sizes], pvalues, color=colors, alpha=0.7)
    ax2.axhline(y=0.05, color='red', linestyle='--', alpha=0.5, label='Significance Level (α=0.05)')
    ax2.set_title('Chi-Square Test P-Values', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Window Size (draws)', fontsize=10)
    ax2.set_ylabel('P-Value', fontsize=10)
    ax2.grid(axis='y', alpha=0.3)
    ax2.legend()
    
    # Add labels
    for i, (ws, chi2, pv) in enumerate(zip(window_sizes, chi2_stats, pvalues)):
        ax1.text(i, chi2, f'{chi2:.2f}', ha='center', va='bottom', fontsize=9)
        ax2.text(i, pv, f'{pv:.3f}', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f'chi_square_tests_{datetime.now().strftime("%Y%m%d")}.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved chi-square test visualization to: {output_file}")


def visualize_rolling_windows_comparison(window_analyses, output_dir='output'):
    """
    Visualize comparison of probabilities across different rolling window sizes.
    
    Args:
        window_analyses: Dictionary with window_size as key and analysis results as value
        output_dir: Directory to save the plot
    """
    fig, ax = plt.subplots(figsize=(14, 6))
    
    digits = sorted([str(d) for d in range(10)])
    x = np.arange(len(digits))
    width = 0.35
    
    window_sizes = sorted(window_analyses.keys())
    num_windows = len(window_sizes)
    
    if num_windows == 1:
        width = 0.6
        offset = 0
    else:
        width = 0.8 / num_windows
        offset = -width * (num_windows - 1) / 2
    
    colors = plt.cm.viridis(np.linspace(0, 1, num_windows))
    
    for idx, window_size in enumerate(window_sizes):
        probabilities = window_analyses[window_size]['probabilities']
        probs = [probabilities[d] for d in digits]
        
        bars = ax.bar(x + offset + idx * width, probs, width, 
                     label=f'{window_size} draws', color=colors[idx], alpha=0.7)
        
        # Add value labels on bars
        for i, p in enumerate(probs):
            if p > 0.05:  # Only label significant probabilities
                ax.text(i + offset + idx * width, p, f'{p:.3f}', 
                       ha='center', va='bottom', fontsize=7, rotation=90)
    
    ax.axhline(y=0.1, color='gray', linestyle='--', alpha=0.5, label='Uniform (10%)')
    ax.set_xlabel('First Digit', fontsize=11)
    ax.set_ylabel('Probability', fontsize=11)
    ax.set_title('Bayesian-Smoothed Probabilities: Rolling Windows Comparison', fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(digits)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f'rolling_windows_comparison_{datetime.now().strftime("%Y%m%d")}.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved rolling windows comparison to: {output_file}")


def visualize_backtest_results(backtest_results, output_dir='output'):
    """
    Visualize backtest accuracy results.
    
    Args:
        backtest_results: Dictionary of backtest results
        output_dir: Directory to save the plot
    """
    if not backtest_results:
        return
    
    fig, axes = plt.subplots(2, 1, figsize=(12, 10))
    
    # Accuracy by Top-K
    window_sizes = sorted(backtest_results.keys())
    top_k_list = sorted(list(backtest_results[window_sizes[0]]['accuracy'].keys()))
    
    x = np.arange(len(window_sizes))
    width = 0.25
    multiplier = 0
    
    for top_k in top_k_list:
        accuracies = []
        baseline_val = top_k / 10.0 * 100
        for ws in window_sizes:
            acc_data = backtest_results[ws]['accuracy'][top_k]
            if acc_data['total'] > 0:
                accuracies.append(acc_data['rate'] * 100)
            else:
                accuracies.append(0)
        
        offset = width * multiplier
        bars = axes[0].bar(x + offset, accuracies, width, label=f'Top-{top_k} Accuracy', alpha=0.8)
        # Add value labels on bars
        for i, acc in enumerate(accuracies):
            axes[0].text(i + offset, acc, f'{acc:.1f}%', ha='center', va='bottom', fontsize=8)
        # Draw baseline as horizontal line (only once per top_k)
        if multiplier == 0:
            axes[0].axhline(y=baseline_val, color='gray', linestyle='--', alpha=0.5, linewidth=1.5, 
                           label=f'Baseline ({baseline_val:.1f}%)')
        multiplier += 1
    
    axes[0].set_xlabel('Window Size (draws)', fontsize=10)
    axes[0].set_ylabel('Accuracy (%)', fontsize=10)
    axes[0].set_title('Backtest Accuracy by Top-K Predictions', fontsize=12, fontweight='bold')
    axes[0].set_xticks(x + width, [str(ws) for ws in window_sizes])
    axes[0].legend()
    axes[0].grid(axis='y', alpha=0.3)
    
    # Chi-square test summary
    uniform_counts = []
    non_uniform_counts = []
    for ws in window_sizes:
        chi2 = backtest_results[ws]['chi2_tests']
        uniform_counts.append(chi2['uniform'])
        non_uniform_counts.append(chi2['non_uniform'])
    
    x2 = np.arange(len(window_sizes))
    width2 = 0.35
    axes[1].bar(x2 - width2/2, uniform_counts, width2, label='Uniform Distribution', color='green', alpha=0.7)
    axes[1].bar(x2 + width2/2, non_uniform_counts, width2, label='Non-Uniform Distribution', color='red', alpha=0.7)
    axes[1].set_xlabel('Window Size (draws)', fontsize=10)
    axes[1].set_ylabel('Number of Tests', fontsize=10)
    axes[1].set_title('Chi-Square Test Results Distribution', fontsize=12, fontweight='bold')
    axes[1].set_xticks(x2, [str(ws) for ws in window_sizes])
    axes[1].legend()
    axes[1].grid(axis='y', alpha=0.3)
    
    # Add value labels
    for i, (u, nu) in enumerate(zip(uniform_counts, non_uniform_counts)):
        axes[1].text(i - width2/2, u, str(u), ha='center', va='bottom', fontsize=9)
        axes[1].text(i + width2/2, nu, str(nu), ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f'backtest_results_{datetime.now().strftime("%Y%m%d")}.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved backtest results visualization to: {output_file}")

