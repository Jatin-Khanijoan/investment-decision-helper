#!/usr/bin/env python3
"""
Run full backtesting comparison: equal weights vs expert weights vs RL weights.
Train on Jan-Jun 2025, test on Jul-Jan 2026.
"""
import logging
from datetime import datetime
import json
from data_accessor import NiftyDataAccessor
from database import DatabaseManager
from weight_manager import WeightManager
from rl_learner import ThompsonSamplingLearner
from backtester import Backtester

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def save_results_to_json(results_dict, filename="backtest_results.json"):
    """Save results to JSON file."""
    # Convert DecisionRecords to dicts
    serializable = {}
    for key, records in results_dict.items():
        serializable[key] = [
            {
                'timestamp': r.timestamp,
                'symbol': r.symbol,
                'decision': r.decision,
                'confidence': r.confidence,
                'regime': r.market_regime,
                'outcome_7d': r.outcome_7d,
                'reward': r.reward,
                'evaluated': r.evaluated
            }
            for r in records
        ]
    
    with open(filename, 'w') as f:
        json.dump(serializable, f, indent=2)
    logger.info(f"Saved results to {filename}")


def calculate_metrics(results):
    """Calculate performance metrics."""
    if not results:
        return {}
    
    correct = 0
    total = len(results)
    total_reward = 0.0
    returns = []
    
    for r in results:
        # Check correctness
        if r.decision == "BUY" and r.outcome_7d > 1.0:
            correct += 1
        elif r.decision == "SELL" and r.outcome_7d < -1.0:
            correct += 1
        elif r.decision == "HOLD" and abs(r.outcome_7d) < 2.0:
            correct += 1
            
        total_reward += r.reward
        returns.append(r.outcome_7d)
    
    import numpy as np
    
    metrics = {
        'total_decisions': total,
        'correct_decisions': correct,
        'accuracy': (correct / total) * 100 if total > 0 else 0,
        'avg_reward': total_reward / total if total > 0 else 0,
        'avg_return': np.mean(returns) if returns else 0,
        'std_return': np.std(returns) if returns else 0,
        'sharpe_ratio': (np.mean(returns) / np.std(returns)) if returns and np.std(returns) > 0 else 0
    }
    
    return metrics


def main():
    logger.info("=" * 80)
    logger.info("BACKTESTING: RL-BASED INVESTMENT DECISION SYSTEM")
    logger.info("=" * 80)
    
    # Initialize components
    logger.info("\nInitializing components...")
    data = NiftyDataAccessor()
    db = DatabaseManager("backtest_full.db")
    rl_learner = ThompsonSamplingLearner(db)
    weight_manager = WeightManager(rl_learner=rl_learner)
    backtester = Backtester(data, db, weight_manager, rl_learner)
    
    # Define periods
    train_start = datetime(2025, 1, 23)
    train_end = datetime(2025, 6, 30)
    test_start = datetime(2025, 7, 1)
    test_end = datetime(2026, 1, 15)  # Leave buffer for 7-day forward
    
    logger.info(f"Training period: {train_start.date()} to {train_end.date()}")
    logger.info(f"Testing period: {test_start.date()} to {test_end.date()}")
    
    # Storage for results
    all_results = {}
    
    # ========================================================================
    # PHASE 1: TRAINING (Jan-Jun 2025)
    # ========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 1: TRAINING (Jan-Jun 2025)")
    logger.info("=" * 80)
    
    num_train_decisions = 75
    
    # 1.1: Equal Weights (Training)
    logger.info("\n[1/6] Running Equal Weights - Training...")
    train_equal = backtester.run_backtest(
        train_start, train_end,
        system_type='equal_weights',
        num_decisions=num_train_decisions,
        enable_rl_learning=False
    )
    all_results['train_equal'] = train_equal
    
    # 1.2: Expert Weights (Training)
    logger.info("\n[2/6] Running Expert Weights - Training...")
    train_expert = backtester.run_backtest(
        train_start, train_end,
        system_type='expert_weights',
        num_decisions=num_train_decisions,
        enable_rl_learning=False
    )
    all_results['train_expert'] = train_expert
    
    # 1.3: RL Weights (Training - WITH LEARNING)
    logger.info("\n[3/6] Running RL Weights - Training (Learning Enabled)...")
    train_rl = backtester.run_backtest(
        train_start, train_end,
        system_type='rl_weights',
        num_decisions=num_train_decisions,
        enable_rl_learning=True  # RL learns during training!
    )
    all_results['train_rl'] = train_rl
    
    # Training results
    logger.info("\n" + "=" * 80)
    logger.info("TRAINING RESULTS")
    logger.info("=" * 80)
    
    for system_name, results in [
        ('Equal Weights', train_equal),
        ('Expert Weights', train_expert),
        ('RL Weights', train_rl)
    ]:
        metrics = calculate_metrics(results)
        logger.info(f"\n{system_name}:")
        logger.info(f"  Accuracy: {metrics['accuracy']:.1f}% ({metrics['correct_decisions']}/{metrics['total_decisions']})")
        logger.info(f"  Avg Reward: {metrics['avg_reward']:.3f}")
        logger.info(f"  Avg Return: {metrics['avg_return']:.2f}%")
        logger.info(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.3f}")
    
    # ========================================================================
    # PHASE 2: TESTING (Jul-Jan 2026)
    # ========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 2: TESTING (Jul-Jan 2026) - RL LEARNING FROZEN")
    logger.info("=" * 80)
    
    num_test_decisions = 75
    
    # 2.1: Equal Weights (Testing)
    logger.info("\n[4/6] Running Equal Weights - Testing...")
    test_equal = backtester.run_backtest(
        test_start, test_end,
        system_type='equal_weights',
        num_decisions=num_test_decisions,
        enable_rl_learning=False
    )
    all_results['test_equal'] = test_equal
    
    # 2.2: Expert Weights (Testing)
    logger.info("\n[5/6] Running Expert Weights - Testing...")
    test_expert = backtester.run_backtest(
        test_start, test_end,
        system_type='expert_weights',
        num_decisions=num_test_decisions,
        enable_rl_learning=False
    )
    all_results['test_expert'] = test_expert
    
    # 2.3: RL Weights (Testing - NO LEARNING)
    logger.info("\n[6/6] Running RL Weights - Testing (Frozen Weights)...")
    test_rl = backtester.run_backtest(
        test_start, test_end,
        system_type='rl_weights',
        num_decisions=num_test_decisions,
        enable_rl_learning=False  # RL frozen during testing!
    )
    all_results['test_rl'] = test_rl
    
    # Testing results
    logger.info("\n" + "=" * 80)
    logger.info("TESTING RESULTS (Generalization)")
    logger.info("=" * 80)
    
    for system_name, results in [
        ('Equal Weights', test_equal),
        ('Expert Weights', test_expert),
        ('RL Weights', test_rl)
    ]:
        metrics = calculate_metrics(results)
        logger.info(f"\n{system_name}:")
        logger.info(f"  Accuracy: {metrics['accuracy']:.1f}% ({metrics['correct_decisions']}/{metrics['total_decisions']})")
        logger.info(f"  Avg Reward: {metrics['avg_reward']:.3f}")
        logger.info(f"  Avg Return: {metrics['avg_return']:.2f}%")
        logger.info(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.3f}")
    
    # ========================================================================
    # FINAL COMPARISON
    # ========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("FINAL COMPARISON SUMMARY")
    logger.info("=" * 80)
    
    summary = []
    for phase, systems in [
        ("Training", [train_equal, train_expert, train_rl]),
        ("Testing", [test_equal, test_expert, test_rl])
    ]:
        logger.info(f"\n{phase} Phase:")
        phase_metrics = []
        for system_name, results in zip(['Equal', 'Expert', 'RL'], systems):
            m = calculate_metrics(results)
            phase_metrics.append(m)
            logger.info(f"  {system_name:12s}: {m['accuracy']:5.1f}% acc, {m['avg_reward']:6.3f} reward")
        summary.append((phase, phase_metrics))
    
    # Save results
    save_results_to_json(all_results, "backtest_results.json")
    
    # Close database
    db.close()
    
    logger.info("\n" + "=" * 80)
    logger.info("BACKTESTING COMPLETE")
    logger.info("=" * 80)
    logger.info("\nResults saved to: backtest_results.json")
    logger.info("Database saved to: backtest_full.db")


if __name__ == "__main__":
    main()
