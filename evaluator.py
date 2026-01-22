"""
Statistical evaluation and proof generation for backtest results.
Analyzes performance, generates comparisons, and creates visualizations.
"""
import json
import logging
from typing import Dict, List, Tuple
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

logger = logging.getLogger(__name__)

# Set style for plots
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)


class BacktestEvaluator:
    """
    Evaluates backtest results and generates statistical proofs.
    """
    
    def __init__(self, results_file: str = "backtest_results.json"):
        """
        Initialize evaluator with results file.
        
        Args:
            results_file: Path to backtest results JSON
        """
        self.results_file = results_file
        self.results = self.load_results()
        
    def load_results(self) -> Dict:
        """Load results from JSON file."""
        with open(self.results_file, 'r') as f:
            return json.load(f)
            
    def calculate_metrics(self, decisions: List[Dict]) -> Dict:
        """
        Calculate comprehensive metrics for a set of decisions.
        
        Args:
            decisions: List of decision records
            
        Returns:
            Dictionary of metrics
        """
        if not decisions:
            return {}
            
        correct = 0
        total = len(decisions)
        rewards = []
        returns = []
        
        # By decision type
        buy_correct = sell_correct = hold_correct = 0
        buy_total = sell_total = hold_total = 0
        
        for d in decisions:
            decision = d['decision']
            outcome = d['outcome_7d']
            reward = d['reward']
            
            # Overall correctness
            if decision == 'BUY' and outcome > 1.0:
                correct += 1
                buy_correct += 1
            elif decision == 'SELL' and outcome < -1.0:
                correct += 1
                sell_correct += 1
            elif decision == 'HOLD' and abs(outcome) < 2.0:
                correct += 1
                hold_correct += 1
                
            # Count by type
            if decision == 'BUY':
                buy_total += 1
            elif decision == 'SELL':
                sell_total += 1
            else:
                hold_total += 1
                
            rewards.append(reward)
            returns.append(outcome)
            
        metrics = {
            'total_decisions': total,
            'correct': correct,
            'accuracy': (correct / total * 100) if total > 0 else 0,
            'avg_reward': np.mean(rewards),
            'std_reward': np.std(rewards),
            'avg_return': np.mean(returns),
            'std_return': np.std(returns),
            'sharpe_ratio': (np.mean(returns) / np.std(returns)) if np.std(returns) > 0 else 0,
            'max_return': np.max(returns),
            'min_return': np.min(returns),
            'buy_accuracy': (buy_correct / buy_total * 100) if buy_total > 0 else 0,
            'sell_accuracy': (sell_correct / sell_total * 100) if sell_total > 0 else 0,
            'hold_accuracy': (hold_correct / hold_total * 100) if hold_total > 0 else 0,
            'buy_count': buy_total,
            'sell_count': sell_total,
            'hold_count': hold_total
        }
        
        return metrics
        
    def statistical_comparison(
        self, 
        system1_decisions: List[Dict],
        system2_decisions: List[Dict],
        system1_name: str = "System 1",
        system2_name: str = "System 2"
    ) -> Dict:
        """
        Perform statistical comparison between two systems.
        
        Args:
            system1_decisions: Decisions from first system
            system2_decisions: Decisions from second system
            system1_name: Name of first system
            system2_name: Name of second system
            
        Returns:
            Comparison statistics
        """
        # Extract rewards
        rewards1 = [d['reward'] for d in system1_decisions]
        rewards2 = [d['reward'] for d in system2_decisions]
        
        # T-test
        t_stat, p_value = stats.ttest_ind(rewards1, rewards2)
        
        # Effect size (Cohen's d)
        mean_diff = np.mean(rewards1) - np.mean(rewards2)
        pooled_std = np.sqrt((np.std(rewards1)**2 + np.std(rewards2)**2) / 2)
        cohens_d = mean_diff / pooled_std if pooled_std > 0 else 0
        
        # Accuracy comparison
        acc1 = self.calculate_metrics(system1_decisions)['accuracy']
        acc2 = self.calculate_metrics(system2_decisions)['accuracy']
        
        comparison = {
            'system1': system1_name,
            'system2': system2_name,
            't_statistic': t_stat,
            'p_value': p_value,
            'significant': p_value < 0.05,
            'cohens_d': cohens_d,
            'effect_size': 'large' if abs(cohens_d) > 0.8 else 'medium' if abs(cohens_d) > 0.5 else 'small',
            'accuracy_diff': acc1 - acc2,
            'reward_diff': np.mean(rewards1) - np.mean(rewards2)
        }
        
        return comparison
        
    def regime_analysis(self) -> Dict[str, Dict]:
        """
        Analyze performance by market regime.
        
        Returns:
            Dictionary of regime-specific metrics
        """
        regime_data = {}
        
        # Aggregate all decisions
        all_decisions = []
        for key in ['train_equal', 'train_expert', 'train_rl', 'test_equal', 'test_expert', 'test_rl']:
            for d in self.results.get(key, []):
                d['system'] = key.split('_')[1]  # equal, expert, or rl
                d['phase'] = key.split('_')[0]  # train or test
                all_decisions.append(d)
                
        # Group by regime
        for decision in all_decisions:
            regime = decision.get('regime', 'unknown')
            if regime not in regime_data:
                regime_data[regime] = {
                    'equal': [],
                    'expert': [],
                    'rl': []
                }
            regime_data[regime][decision['system']].append(decision)
            
        # Calculate metrics per regime
        regime_metrics = {}
        for regime, systems in regime_data.items():
            regime_metrics[regime] = {}
            for system, decisions in systems.items():
                if decisions:
                    regime_metrics[regime][system] = self.calculate_metrics(decisions)
                    
        return regime_metrics
        
    def generate_comparison_table(self) -> str:
        """
        Generate formatted comparison table.
        
        Returns:
            Markdown-formatted table
        """
        lines = []
        lines.append("# Backtest Results Comparison")
        lines.append("")
        
        # Training results
        lines.append("## Training Phase (Jan-Jun 2025)")
        lines.append("")
        lines.append("| System | Accuracy | Avg Reward | Avg Return | Sharpe |")
        lines.append("|--------|----------|------------|------------|--------|")
        
        for system_key, system_name in [('train_equal', 'Equal Weights'), 
                                         ('train_expert', 'Expert Weights'),
                                         ('train_rl', 'RL Weights')]:
            metrics = self.calculate_metrics(self.results.get(system_key, []))
            lines.append(
                f"| {system_name} | {metrics['accuracy']:.1f}% | "
                f"{metrics['avg_reward']:.3f} | {metrics['avg_return']:.2f}% | "
                f"{metrics['sharpe_ratio']:.3f} |"
            )
            
        lines.append("")
        
        # Testing results
        lines.append("## Testing Phase (Jul-Jan 2026)")
        lines.append("")
        lines.append("| System | Accuracy | Avg Reward | Avg Return | Sharpe |")
        lines.append("|--------|----------|------------|------------|--------|")
        
        for system_key, system_name in [('test_equal', 'Equal Weights'), 
                                         ('test_expert', 'Expert Weights'),
                                         ('test_rl', 'RL Weights')]:
            metrics = self.calculate_metrics(self.results.get(system_key, []))
            lines.append(
                f"| {system_name} | {metrics['accuracy']:.1f}% | "
                f"{metrics['avg_reward']:.3f} | {metrics['avg_return']:.2f}% | "
                f"{metrics['sharpe_ratio']:.3f} |"
            )
            
        lines.append("")
        
        # Statistical tests
        lines.append("## Statistical Significance Tests")
        lines.append("")
        
        comp = self.statistical_comparison(
            self.results['test_rl'],
            self.results['test_expert'],
            "RL Weights",
            "Expert Weights"
        )
        
        lines.append(f"**RL vs Expert (Test Set)**:")
        lines.append(f"- p-value: {comp['p_value']:.4f}")
        lines.append(f"- Significant: {'Yes' if comp['significant'] else 'No'} (α=0.05)")
        lines.append(f"- Effect size: {comp['effect_size']} (Cohen's d={comp['cohens_d']:.3f})")
        lines.append(f"- Accuracy difference: {comp['accuracy_diff']:.1f}%")
        
        return "\n".join(lines)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test evaluator
    evaluator = BacktestEvaluator()
    
    print("Loaded results from backtest_results.json")
    print(f"Keys: {list(evaluator.results.keys())}")
    
    # Calculate metrics
    test_rl_metrics = evaluator.calculate_metrics(evaluator.results['test_rl'])
    print(f"\nRL Test Metrics:")
    print(f"  Accuracy: {test_rl_metrics['accuracy']:.1f}%")
    print(f"  Avg Reward: {test_rl_metrics['avg_reward']:.3f}")
    
    # Comparison
    comp = evaluator.statistical_comparison(
        evaluator.results['test_rl'],
        evaluator.results['test_equal'],
        "RL", "Equal"
    )
    print(f"\nRL vs Equal comparison:")
    print(f"  p-value: {comp['p_value']:.4f}")
    print(f"  Significant: {comp['significant']}")
    
    # Generate table
    table = evaluator.generate_comparison_table()
    print("\n" + "="*60)
    print(table)
    
    # Save to file
    with open("backtest_comparison.md", 'w') as f:
        f.write(table)
    print("\nSaved comparison to backtest_comparison.md")
