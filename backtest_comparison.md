# Backtest Results Comparison

## Training Phase (Jan-Jun 2025)

| System | Accuracy | Avg Reward | Avg Return | Sharpe |
|--------|----------|------------|------------|--------|
| Equal Weights | 58.7% | 0.240 | 0.56% | 0.221 |
| Expert Weights | 58.7% | 0.257 | 0.71% | 0.269 |
| RL Weights | 56.0% | 0.202 | 0.52% | 0.199 |

## Testing Phase (Jul-Jan 2026)

| System | Accuracy | Avg Reward | Avg Return | Sharpe |
|--------|----------|------------|------------|--------|
| Equal Weights | 81.3% | 0.458 | -0.03% | -0.019 |
| Expert Weights | 78.7% | 0.435 | 0.11% | 0.077 |
| RL Weights | 74.7% | 0.393 | 0.05% | 0.036 |

## Statistical Significance Tests

**RL vs Expert (Test Set)**:
- p-value: 0.5530
- Significant: No (α=0.05)
- Effect size: small (Cohen's d=-0.098)
- Accuracy difference: -4.0%