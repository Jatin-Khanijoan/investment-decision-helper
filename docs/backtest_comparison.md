# Backtest Results Comparison

## Data Configuration

- **Total Data**: 5 years of NIFTY 50 data (Jan 2021 - Jan 2026)
- **Training Period**: Jan 2021 - Dec 2023 (3 years, 300 decisions)
- **Testing Period**: Jan 2024 - Jan 2026 (2 years, 200 decisions)
- **Total Trading Days**: 1,239

## Training Phase (Jan 2021 - Dec 2023)

| System | Decisions | Accuracy | Avg Reward | Avg Return | Sharpe |
|--------|-----------|----------|------------|------------|--------|
| Equal Weights | 300 | 58.3% | 0.237 | - | - |
| Expert Weights | 300 | 59.7% | 0.267 | - | - |
| RL Weights | 300 | 57.0% | 0.238 | - | - |

## Testing Phase (Jan 2024 - Jan 2026)

| System | Decisions | Accuracy | Avg Reward | Avg Return | Sharpe |
|--------|-----------|----------|------------|------------|--------|
| Equal Weights | 200 | 68.0% | 0.337 | 0.14% | 0.070 |
| Expert Weights | 200 | 67.0% | 0.325 | 0.26% | 0.123 |
| **RL Weights** | **200** | **69.5%** | **0.342** | **0.37%** | **0.188** |

## Key Findings

### RL Outperforms on Test Set

| Metric | RL vs Equal | RL vs Expert |
|--------|-------------|--------------|
| Accuracy | +1.5% | +2.5% |
| Avg Reward | +0.005 | +0.017 |
| Sharpe Ratio | +0.118 | +0.065 |

### Market Conditions Covered

- **2021**: Post-COVID recovery rally
- **2022**: Volatile year with inflation concerns
- **2023**: Market stabilization
- **2024-2026**: New highs and consolidation

### RL Learning Demonstration

The RL system trained on 3 years of diverse market conditions successfully:
- Learned regime-specific weight adjustments
- Generalized to unseen 2-year test period
- Achieved best accuracy (69.5%) and Sharpe ratio (0.188)
- Demonstrates value of adaptive weighting over static approaches