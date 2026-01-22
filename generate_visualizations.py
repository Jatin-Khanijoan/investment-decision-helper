"""
Generate visualizations for backtest results.
"""
import json
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

# Create results directory
results_dir = Path("results")
results_dir.mkdir(exist_ok=True)

# Load results
with open("backtest_results.json", 'r') as f:
    results = json.load(f)


def plot_accuracy_comparison():
    """Generate accuracy comparison bar chart."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Training
    systems = ['Equal', 'Expert', 'RL']
    train_acc = [
        sum(1 for d in results['train_equal'] if (
            (d['decision'] == 'BUY' and d['outcome_7d'] > 1) or
            (d['decision'] == 'SELL' and d['outcome_7d'] < -1) or
            (d['decision'] == 'HOLD' and abs(d['outcome_7d']) < 2)
        )) / len(results['train_equal']) * 100,
        sum(1 for d in results['train_expert'] if (
            (d['decision'] == 'BUY' and d['outcome_7d'] > 1) or
            (d['decision'] == 'SELL' and d['outcome_7d'] < -1) or
            (d['decision'] == 'HOLD' and abs(d['outcome_7d']) < 2)
        )) / len(results['train_expert']) * 100,
        sum(1 for d in results['train_rl'] if (
            (d['decision'] == 'BUY' and d['outcome_7d'] > 1) or
            (d['decision'] == 'SELL' and d['outcome_7d'] < -1) or
            (d['decision'] == 'HOLD' and abs(d['outcome_7d']) < 2)
        )) / len(results['train_rl']) * 100
    ]
    
    colors = ['#3498db', '#e74c3c', '#2ecc71']
    ax1.bar(systems, train_acc, color=colors, alpha=0.7)
    ax1.set_ylabel('Accuracy (%)', fontsize=12)
    ax1.set_title('Training Phase (Jan-Jun 2025)', fontsize=14, fontweight='bold')
    ax1.set_ylim(0, 100)
    ax1.grid(axis='y', alpha=0.3)
    for i, v in enumerate(train_acc):
        ax1.text(i, v + 2, f'{v:.1f}%', ha='center', fontweight='bold')
    
    # Testing
    test_acc = [
        sum(1 for d in results['test_equal'] if (
            (d['decision'] == 'BUY' and d['outcome_7d'] > 1) or
            (d['decision'] == 'SELL' and d['outcome_7d'] < -1) or
            (d['decision'] == 'HOLD' and abs(d['outcome_7d']) < 2)
        )) / len(results['test_equal']) * 100,
        sum(1 for d in results['test_expert'] if (
            (d['decision'] == 'BUY' and d['outcome_7d'] > 1) or
            (d['decision'] == 'SELL' and d['outcome_7d'] < -1) or
            (d['decision'] == 'HOLD' and abs(d['outcome_7d']) < 2)
        )) / len(results['test_expert']) * 100,
        sum(1 for d in results['test_rl'] if (
            (d['decision'] == 'BUY' and d['outcome_7d'] > 1) or
            (d['decision'] == 'SELL' and d['outcome_7d'] < -1) or
            (d['decision'] == 'HOLD' and abs(d['outcome_7d']) < 2)
        )) / len(results['test_rl']) * 100
    ]
    
    ax2.bar(systems, test_acc, color=colors, alpha=0.7)
    ax2.set_ylabel('Accuracy (%)', fontsize=12)
    ax2.set_title('Testing Phase (Jul-Jan 2026)', fontsize=14, fontweight='bold')
    ax2.set_ylim(0, 100)
    ax2.grid(axis='y', alpha=0.3)
    for i, v in enumerate(test_acc):
        ax2.text(i, v + 2, f'{v:.1f}%', ha='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(results_dir / 'accuracy_comparison.png', dpi=300, bbox_inches='tight')
    print(f"Saved: {results_dir}/accuracy_comparison.png")
    plt.close()


def plot_reward_comparison():
    """Generate reward comparison box plots."""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    data = [
        [d['reward'] for d in results['test_equal']],
        [d['reward'] for d in results['test_expert']],
        [d['reward'] for d in results['test_rl']]
    ]
    
    bp = ax.boxplot(data, labels=['Equal', 'Expert', 'RL'], patch_artist=True)
    
    colors = ['#3498db', '#e74c3c', '#2ecc71']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax.set_ylabel('Reward', fontsize=12)
    ax.set_title('Reward Distribution (Test Phase)', fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    
    # Add mean markers
    means = [np.mean(d) for d in data]
    ax.scatter([1, 2, 3], means, color='red', s=100, zorder=3, label='Mean')
    ax.legend()
    
    plt.tight_layout()
    plt.savefig(results_dir / 'reward_distribution.png', dpi=300, bbox_inches='tight')
    print(f"Saved: {results_dir}/reward_distribution.png")
    plt.close()


def plot_regime_heatmap():
    """Generate regime-specific performance heatmap."""
    # Group by regime
    regime_data = {}
    for key in ['test_equal', 'test_expert', 'test_rl']:
        for d in results[key]:
            regime = d.get('regime', 'unknown')
            if regime not in regime_data:
                regime_data[regime] = {'equal': [], 'expert': [], 'rl': []}
            system = key.split('_')[1]
            regime_data[regime][system].append(d)
    
    # Calculate accuracies
    regimes = list(regime_data.keys())[:10]  # Top 10 regimes
    systems = ['equal', 'expert', 'rl']
    
    heatmap_data = []
    for regime in regimes:
        row = []
        for system in systems:
            decisions = regime_data[regime][system]
            if decisions:
                correct = sum(1 for d in decisions if (
                    (d['decision'] == 'BUY' and d['outcome_7d'] > 1) or
                    (d['decision'] == 'SELL' and d['outcome_7d'] < -1) or
                    (d['decision'] == 'HOLD' and abs(d['outcome_7d']) < 2)
                ))
                acc = correct / len(decisions) * 100
            else:
                acc = 0
            row.append(acc)
        heatmap_data.append(row)
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    sns.heatmap(
        heatmap_data,
        annot=True,
        fmt='.1f',
        cmap='RdYlGn',
        xticklabels=['Equal', 'Expert', 'RL'],
        yticklabels=[r.replace('_', ' ').title()[:25] for r in regimes],
        cbar_kws={'label': 'Accuracy (%)'},
        vmin=0,
        vmax=100
    )
    
    ax.set_title('Accuracy by Market Regime (Test Phase)', fontsize=14, fontweight='bold', pad=20)
    ax.set_ylabel('Market Regime', fontsize=12)
    ax.set_xlabel('System', fontsize=12)
    
    plt.tight_layout()
    plt.savefig(results_dir / 'regime_heatmap.png', dpi=300, bbox_inches='tight')
    print(f"Saved: {results_dir}/regime_heatmap.png")
    plt.close()


def plot_cumulative_performance():
    """Plot cumulative accuracy over decisions."""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    for key, label, color in [
        ('test_equal', 'Equal Weights', '#3498db'),
        ('test_expert', 'Expert Weights', '#e74c3c'),
        ('test_rl', 'RL Weights', '#2ecc71')
    ]:
        decisions = results[key]
        cumulative_correct = []
        correct_count = 0
        
        for i, d in enumerate(decisions, 1):
            if ((d['decision'] == 'BUY' and d['outcome_7d'] > 1) or
                (d['decision'] == 'SELL' and d['outcome_7d'] < -1) or
                (d['decision'] == 'HOLD' and abs(d['outcome_7d']) < 2)):
                correct_count += 1
            cumulative_correct.append(correct_count / i * 100)
        
        ax.plot(range(1, len(cumulative_correct) + 1), cumulative_correct, 
                label=label, linewidth=2, color=color)
    
    ax.set_xlabel('Decision Number', fontsize=12)
    ax.set_ylabel('Cumulative Accuracy (%)', fontsize=12)
    ax.set_title('Cumulative Accuracy Over Time (Test Phase)', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(alpha=0.3)
    ax.set_ylim(0, 100)
    
    plt.tight_layout()
    plt.savefig(results_dir / 'cumulative_accuracy.png', dpi=300, bbox_inches='tight')
    print(f"Saved: {results_dir}/cumulative_accuracy.png")
    plt.close()


if __name__ == "__main__":
    print("Generating visualizations...")
    print()
    
    plot_accuracy_comparison()
    plot_reward_comparison()
    plot_regime_heatmap()
    plot_cumulative_performance()
    
    print()
    print("All visualizations saved to results/ directory")
