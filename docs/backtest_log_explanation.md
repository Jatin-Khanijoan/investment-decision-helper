# Backtest Log Explanation

This log shows the training phase of an RL-based investment decision system being backtested on 5 years of NIFTY 50 (Indian stock index) data.

## System Initialization (Lines 1-20)

- Loaded 5 CSV files containing NIFTY 50 data from Jan 2021 to Jan 2026
- 1,239 total trading days loaded
- Data split:
  - **Training:** 743 days (Jan 2021 - Jan 2024)
  - **Testing:** 496 days (Jan 2024 - Jan 2026)
- Database initialized at `backtest_full.db`

## Phase 1: Training with Equal Weights (Lines 29-200)

The system runs the first strategy called "Equal Weights" (a baseline without RL learning) making 300 trading decisions.

### Decision Types & Rewards

Each decision is one of: **BUY**, **SELL**, or **HOLD**

| Outcome            | Reward Range | Example                                                 |
|--------------------|--------------|--------------------------------------------------------|
| Correct prediction | +0.6 to +1.4 | `Reward: 1.326 for BUY (return=2.52%, correct=True)`   |
| Wrong prediction   | -0.2 to -0.8 | `Reward: -0.800 for SELL (return=3.88%, correct=False)` |

The reward magnitude depends on:

- **Return %:** Larger moves = bigger reward/penalty
- **Confidence:** Higher confidence = amplified reward/penalty

### Progress Checkpoints

| Decisions | Accuracy |
|-----------|----------|
| 25/300    | 28.0%    |
| 50/300    | 52.0%    |
| 100/300   | 53.0%    |
| 150/300   | 49.3%    |

The ~50% accuracy indicates the Equal Weights baseline performs at near-random level, which is expected since it doesn't use learned weights. This establishes a baseline to compare against RL-trained strategies.
