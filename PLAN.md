# RL Implementation Plan for Kautilya
**Goal**: Add Reinforcement Learning-based weight adaptation to demonstrate improved investment decisions

---



## Phase 4: RL Implementation

### Step 4.1: Feature Vector Construction
- [ ] Create `rl_features.py` module
- [ ] Build function to convert `MarketRegime` to state vector
- [ ] One-hot encode inflation (3 dims), rate trend (3 dims), sentiment (3 dims)
- [ ] Add volatility as continuous feature (1 dim)
- [ ] Add sector encoding (5 dims for major sectors)
- [ ] Add time context if available (1 dim)
- [ ] Total: ~16-dimensional state vector

### Step 4.2: Thompson Sampling Learner
- [ ] Create `rl_learner.py` module
- [ ] Build `ThompsonSamplingLearner` class
- [ ] Initialize: Create alpha/beta arrays for each (regime, agent) pair
- [ ] Method: `select_weights(regime)` - sample from Beta distribution per agent
- [ ] Method: `normalize_sampled_weights(samples)` - ensure sum to 1.0
- [ ] Method: `get_regime_key(regime)` - convert regime to unique string key
- [ ] Store/load alpha/beta state from database

### Step 4.3: Reward Calculator
- [ ] Create `reward_calculator.py` module
- [ ] Build `calculate_reward(decision, price_at_decision, price_after_7d, confidence)` function
- [ ] Component 1: Directional accuracy (BUY+up=+1.0, SELL+down=+1.0, HOLD+stable=+0.5, wrong=-0.5)
- [ ] Component 2: Confidence calibration (confident+correct=+0.2, confident+wrong=-0.3)
- [ ] Component 3: Magnitude bonus (scale by return percentage)
- [ ] Return total reward (range: -0.8 to +1.7)
- [ ] Add logging for reward breakdown

### Step 4.4: Belief Update Mechanism
- [ ] In `ThompsonSamplingLearner`, add method: `update(decision_record, reward)`
- [ ] Extract weights_used from decision_record
- [ ] For each agent, calculate weight_contribution
- [ ] If reward > 0: increment alpha by (weight_contribution × reward)
- [ ] If reward < 0: increment beta by (weight_contribution × |reward|)
- [ ] Save updated alpha/beta to database
- [ ] Log the update for tracking

### Step 4.5: Integration with Weight Manager
- [ ] Modify `WeightManager` to use RL learner
- [ ] Method: `get_rl_adjusted_weights(regime, sector)` 
- [ ] Call base weights + regime multipliers (70% weight)
- [ ] Call RL learner to get learned weights (30% weight)
- [ ] Blend: `final = 0.7 × rl_learned + 0.3 × expert_base`
- [ ] Return final normalized weights
- [ ] Add flag to enable/disable RL (for baseline comparison)

---

## Phase 5: Conversation Context

### Step 5.1: LangGraph Checkpointing Setup
- [ ] Install LangGraph checkpointing dependency
- [ ] Create SQLite checkpointer in `graph.py`
- [ ] Configure thread_id management (generate unique ID per conversation)
- [ ] Test checkpoint saving after each node execution
- [ ] Verify state restoration from checkpoints

### Step 5.2: Conversation History Loading
- [ ] In `graph.py`, add new node: `load_conversation_history`
- [ ] Query database for previous N turns (default N=3)
- [ ] Format previous decisions into concise summary
- [ ] Add to `DecisionState` as `conversation_history` field
- [ ] Ensure history includes: question, symbol, decision, confidence, key_factors

### Step 5.3: Update LLM Prompt with History
- [ ] Modify `decide_with_llm` function in `graph.py`
- [ ] Add conversation history section to prompt
- [ ] Format: "Previous decisions in this conversation: [Turn 1] [Turn 2] [Turn 3]"
- [ ] Instruct LLM to consider consistency with previous recommendations
- [ ] Test that LLM uses context appropriately

---

## Phase 6: Backtesting Framework

### Step 6.1: Backtesting Engine
- [ ] Create `backtester.py` module
- [ ] Build `Backtester` class with CSV data loaded
- [ ] Method: `run_backtest(start_date, end_date, system_type)` 
- [ ] System types: 'equal_weights', 'static_weights', 'rl_weights'
- [ ] For each trading day in range, simulate decisions for random/all stocks
- [ ] Record decisions with timestamps
- [ ] Fast-forward 7 days in CSV, calculate outcomes, compute rewards
- [ ] Update RL weights (only for 'rl_weights' system)
- [ ] Store all results in database

### Step 6.2: Decision Simulation
- [ ] In backtester, create method: `simulate_decision(symbol, date, system_type)`
- [ ] Load CSV data up to that date only (no future leakage)
- [ ] Run agents with historical data (simulate web searches would return historical info)
- [ ] Apply weights based on system_type
- [ ] Generate decision using LLM or rule-based logic
- [ ] Return decision record

### Step 6.3: Outcome Measurement
- [ ] Create method: `measure_outcome(decision_record, csv_data)`
- [ ] Look up price at decision date
- [ ] Look up price 7 days later
- [ ] Calculate return percentage
- [ ] Determine correctness (BUY+positive, SELL+negative, HOLD+neutral)
- [ ] Calculate reward using reward_calculator
- [ ] Update decision_record with outcome and reward
- [ ] Save to database

### Step 6.4: Train/Test Split
- [ ] Define training period: January 2025 - June 2025
- [ ] Define testing period: July 2025 - January 2026
- [ ] Run backtest on training period, allow RL to learn
- [ ] Freeze RL weights at end of training
- [ ] Run backtest on testing period with frozen weights
- [ ] This proves generalization, not overfitting

---

## Phase 7: Explainability & Output Enhancement

### Step 7.1: Weight Explanation Generator
- [ ] Create `explainer.py` module
- [ ] Build function: `generate_weight_explanation(weights, regime, rl_stats)`
- [ ] Describe detected regime in plain language
- [ ] List top 3 weighted agents with rationale
- [ ] Explain why these weights are appropriate for this regime
- [ ] Include learning stats (decisions learned from, accuracy in this regime)
- [ ] Return formatted explanation dict

### Step 7.2: RL Proof Statistics
- [ ] Create function: `generate_rl_proof(regime, rl_learner, decision_history)`
- [ ] Query decision_history for this regime
- [ ] Calculate accuracy with RL weights vs. baseline
- [ ] Show weight evolution (starting vs. current)
- [ ] Show reliability scores per agent
- [ ] Show uncertainty levels
- [ ] Return rl_proof dict

### Step 7.3: Update Decision Output
- [ ] Modify `decide_with_llm` in `graph.py`
- [ ] After getting LLM decision, add weight_explanation
- [ ] Add rl_proof statistics
- [ ] Add regime_detected info
- [ ] Ensure all fields are populated before returning
- [ ] Validate output against updated schema

### Step 7.4: Enhanced LLM Prompt
- [ ] Restructure prompt to show weighted agent outputs
- [ ] Group by priority: HIGH (weight >0.10), MEDIUM (0.05-0.10), LOW (<0.05)
- [ ] Explain why prioritization matters
- [ ] Instruct LLM to focus analysis on high-priority signals
- [ ] Request LLM explain which signals drove the decision
- [ ] Test that LLM respects weighting in its reasoning

---

## Phase 8: Evaluation & Proof Generation

### Step 8.1: Run Complete Backtest
- [ ] Execute full backtest on training data (Jan-Jun 2025)
- [ ] Execute full backtest on testing data (Jul-Jan 2026)
- [ ] Ensure at least 150 total decisions (75 train, 75 test)
- [ ] Verify all outcomes are measured
- [ ] Verify all rewards are calculated
- [ ] Check RL weight updates are happening

### Step 8.2: Baseline Comparison
- [ ] Run equal-weight system on same decisions
- [ ] Run static expert-weight system on same decisions
- [ ] Ensure all three systems evaluate identical scenarios
- [ ] Store results in separate tables/columns for comparison

### Step 8.3: Statistical Analysis
- [ ] Create `evaluator.py` module
- [ ] Calculate accuracy for each system (train and test sets)
- [ ] Calculate precision, recall, F1 if applicable
- [ ] Compute confidence calibration scores
- [ ] Run t-test to check statistical significance
- [ ] Calculate confidence intervals
- [ ] Generate comparison report

### Step 8.4: Regime-Specific Analysis
- [ ] Group decisions by detected regime
- [ ] Calculate accuracy per regime for each system
- [ ] Identify where RL outperforms most
- [ ] Identify where RL underperforms (if any)
- [ ] Create regime-specific performance tables

### Step 8.5: Visualization Generation
- [ ] Create `visualizer.py` module
- [ ] Generate weight evolution line chart (15 agents over time)
- [ ] Generate accuracy improvement curve (cumulative over decisions)
- [ ] Generate regime heatmap (regimes × agents, color = weight)
- [ ] Generate confidence calibration plot (predicted vs actual)
- [ ] Generate comparison bar chart (3 systems × accuracy)
- [ ] Save all plots to `results/` folder

---

## Phase 9: Dashboard & Demonstration

### Step 9.1: Streamlit Dashboard Enhancements
- [ ] Add new page: "RL Performance Analysis"
- [ ] Display accuracy comparison table
- [ ] Show weight evolution charts
- [ ] Show regime heatmap
- [ ] Add interactive regime selector to see weights change
- [ ] Display statistical significance results
- [ ] Add downloadable CSV of results

### Step 9.2: Live RL Indicator
- [ ] In main decision UI, add "RL Status" badge
- [ ] Show: "Learning Enabled", "Decisions Learned From: 247"
- [ ] Display current regime and top 3 weighted agents
- [ ] Show link to full weight explanation
- [ ] Make it clear RL is actively being used

### Step 9.3: Decision Comparison View
- [ ] Add feature: "Show Alternative Decisions"
- [ ] For current query, show what each system would recommend
- [ ] Display: Equal weights → HOLD (0.5), Expert weights → BUY (0.6), RL weights → BUY (0.8)
- [ ] Highlight differences in confidence and reasoning
- [ ] Explain why RL is more/less confident

### Step 9.4: Historical Decision Viewer
- [ ] Add page to browse past decisions
- [ ] Filter by date, symbol, regime, system type
- [ ] Show outcomes and rewards
- [ ] Allow clicking decision to see full details
- [ ] Show which decisions contributed to learning

---

## Phase 10: Documentation & Final Proof

### Step 10.1: Create Proof Document
- [ ] Write `RL_PROOF_REPORT.md`
- [ ] Section 1: Executive Summary (key results)
- [ ] Section 2: Methodology (train/test split, systems compared)
- [ ] Section 3: Results (accuracy tables, statistical tests)
- [ ] Section 4: Regime Analysis (where RL excels)
- [ ] Section 5: Visualizations (embed charts)
- [ ] Section 6: Limitations & Future Work
- [ ] Section 7: Conclusion

### Step 10.2: Technical Documentation
- [ ] Document RL algorithm choice and rationale
- [ ] Document reward function design
- [ ] Document weight blending strategy (70% RL, 30% expert)
- [ ] Document feature vector construction
- [ ] Add inline comments explaining Thompson Sampling
- [ ] Create architecture diagram showing RL integration

### Step 10.3: User Guide
- [ ] Write guide on interpreting weight explanations
- [ ] Explain what RL statistics mean
- [ ] Explain how to read regime heatmaps
- [ ] Add FAQ: "How does RL make decisions better?"
- [ ] Add example walkthroughs

### Step 10.4: Demo Preparation
- [ ] Prepare 3 example scenarios showcasing RL
- [ ] Scenario 1: High inflation regime (macro weights dominate)
- [ ] Scenario 2: Stable market (company fundamentals dominate)
- [ ] Scenario 3: Regime shift (watch weights adapt)
- [ ] Create slide deck with key visualizations
- [ ] Prepare talking points for each proof element
