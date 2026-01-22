"""
Backtesting engine for RL-based investment decision system.
Simulates decisions on historical NIFTY 50 data to prove RL effectiveness.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import random
import numpy as np

from data_accessor import NiftyDataAccessor
from database import DatabaseManager
from weight_manager import WeightManager
from rl_learner import ThompsonSamplingLearner
from rl_models import MarketRegime, DecisionRecord
from reward_calculator import calculate_reward
from weights_config import ALL_AGENTS, get_base_weights, normalize_weights

logger = logging.getLogger(__name__)


class Backtester:
    """
    Backtesting engine for investment decision systems.
    Simulates decisions on historical data to evaluate performance.
    """
    
    def __init__(
        self,
        data_accessor: NiftyDataAccessor,
        db: DatabaseManager,
        weight_manager: WeightManager,
        rl_learner: Optional[ThompsonSamplingLearner] = None
    ):
        """
        Initialize backtester.
        
        Args:
            data_accessor: Data accessor for NIFTY prices
            db: Database manager
            weight_manager: Weight manager
            rl_learner: Optional RL learner for RL system
        """
        self.data = data_accessor
        self.db = db
        self.weight_manager = weight_manager
        self.rl_learner = rl_learner
        
    def generate_mock_regime(self, date: datetime) -> MarketRegime:
        """
        Generate market regime from technical indicators.
        
        Args:
            date: Date to analyze
            
        Returns:
            MarketRegime object
        """
        # Get historical window for analysis
        window = self.data.get_historical_window(date, days=20, include_end_date=True)
        
        if len(window) < 10:
            # Not enough data, return default regime
            return MarketRegime(
                inflation="medium",
                rate_trend="stable",
                sentiment="neutral",
                volatility=0.15
            )
        
        # Calculate volatility from recent data
        returns = window['Close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)  # Annualized
        
        # Detect trend
        sma_short = window['Close'].tail(5).mean()
        sma_long = window['Close'].tail(20).mean()
        trend = (sma_short - sma_long) / sma_long
        
        # Classify regime components
        # Inflation (use volatility as proxy - high vol = uncertain = high inflation concern)
        if volatility > 0.25:
            inflation = "high"
        elif volatility < 0.15:
            inflation = "low"
        else:
            inflation = "medium"
            
        # Rate trend (inverse of market trend - falling market = rising rates concern)
        if trend < -0.02:
            rate_trend = "rising"
        elif trend > 0.02:
            rate_trend = "falling"
        else:
            rate_trend = "stable"
            
        # Sentiment (based on recent performance)
        recent_return = (window['Close'].iloc[-1] - window['Close'].iloc[-5]) / window['Close'].iloc[-5]
        if recent_return > 0.03:
            sentiment = "bullish"
        elif recent_return < -0.03:
            sentiment = "bearish"
        else:
            sentiment = "neutral"
            
        regime = MarketRegime(
            inflation=inflation,
            rate_trend=rate_trend,
            sentiment=sentiment,
            volatility=volatility
        )
        
        logger.debug(f"Generated regime for {date.date()}: {regime.to_key()}, vol={volatility:.3f}")
        return regime
        
    def make_simple_decision(
        self,
        date: datetime,
        regime: MarketRegime,
        weights: Dict[str, float]
    ) -> Tuple[str, float]:
        """
        Make a simple rule-based decision using weights.
        
        Args:
            date: Decision date
            regime: Market regime
            weights: Agent weights
            
        Returns:
            Tuple of (decision, confidence)
        """
        # Get recent price action
        window = self.data.get_historical_window(date, days=10, include_end_date=True)
        
        if len(window) < 5:
            return "HOLD", 0.3
        
        # Calculate momentum
        recent_prices = window['Close'].tail(5)
        momentum = (recent_prices.iloc[-1] - recent_prices.iloc[0]) / recent_prices.iloc[0]
        
        # Create weighted signal based on regime and momentum
        # Higher macro weights in high inflation/rising rates -> more bearish
        macro_weight = weights.get('inflation', 0) + weights.get('interest_rates', 0) + weights.get('gdp_growth', 0)
        company_weight = sum(weights.get(agent, 0) for agent in ['current', 'financial_performance', 'earnings_volatility'])
        
        # Signal components
        signal = 0.0
        
        # Momentum component (40%)
        signal += momentum * 0.4
        
        # Regime component (30%)
        if regime.sentiment == "bullish":
            signal += 0.03
        elif regime.sentiment == "bearish":
            signal -= 0.03
            
        # Weight balance component (30%)
        # More macro weight = more defensive = negative signal
        # More company weight = more growth-focused = positive signal
        weight_signal = (company_weight - macro_weight) * 0.5
        signal += weight_signal * 0.3
        
        # Determine decision
        if signal > 0.02:
            decision = "BUY"
            confidence = min(0.9, 0.5 + abs(signal) * 10)
        elif signal < -0.02:
            decision = "SELL"
            confidence = min(0.9, 0.5 + abs(signal) * 10)
        else:
            decision = "HOLD"
            confidence = 0.6 - abs(signal) * 5
            
        logger.debug(
            f"Decision for {date.date()}: {decision} (conf={confidence:.2f}), "
            f"signal={signal:.4f}, momentum={momentum:.4f}"
        )
        
        return decision, confidence
        
    def simulate_decision(
        self,
        date: datetime,
        system_type: str
    ) -> DecisionRecord:
        """
        Simulate a decision on a specific date.
        
        Args:
            date: Date to make decision
            system_type: 'equal_weights', 'expert_weights', or 'rl_weights'
            
        Returns:
            DecisionRecord
        """
        # Generate regime
        regime = self.generate_mock_regime(date)
        
        # Get weights based on system type
        if system_type == 'equal_weights':
            weights = {agent: 1.0 / len(ALL_AGENTS) for agent in ALL_AGENTS}
        elif system_type == 'expert_weights':
            # Use weight manager without RL
            weights, _, _ = self.weight_manager.get_final_weights(
                state={'agent_outputs': {}},  # Minimal state
                sector=None,
                use_rl=False,
                technical_indicators={'volatility': regime.volatility}
            )
        elif system_type == 'rl_weights':
            # Use weight manager with RL
            weights, _, _ = self.weight_manager.get_final_weights(
                state={'agent_outputs': {}},
                sector=None,
                use_rl=True,
                rl_blend_ratio=0.7,
                technical_indicators={'volatility': regime.volatility}
            )
        else:
            raise ValueError(f"Unknown system type: {system_type}")
            
        # Make decision
        decision, confidence = self.make_simple_decision(date, regime, weights)
        
        # Create decision record
        record = DecisionRecord(
            timestamp=date.isoformat(),
            symbol="NIFTY50",
            sector="Index",
            decision=decision,
            confidence=confidence,
            weights_used=weights,
            market_regime=regime.to_key(),
            agent_outputs={}  # Simplified for backtesting
        )
        
        return record
        
    def measure_outcome(
        self,
        decision_record: DecisionRecord,
        decision_date: datetime
    ) -> Tuple[float, float]:
        """
        Measure outcome of a decision.
        
        Args:
            decision_record: The decision record
            decision_date: Date decision was made
            
        Returns:
            Tuple of (return_pct, reward)
        """
        # Get prices
        price_at = self.data.get_price(decision_date, 'Close')
        price_after = self.data.get_price_after_days(decision_date, days_ahead=7)
        
        if not price_at or not price_after:
            logger.warning(f"Could not get prices for {decision_date.date()}")
            return 0.0, 0.0
            
        # Calculate return
        return_pct = ((price_after - price_at) / price_at) * 100
        
        # Calculate reward
        reward, breakdown = calculate_reward(
            decision_record.decision,
            price_at,
            price_after,
            decision_record.confidence
        )
        
        logger.debug(
            f"Outcome for {decision_date.date()}: {decision_record.decision} → "
            f"{return_pct:.2f}%, reward={reward:.3f}"
        )
        
        return return_pct, reward
        
    def run_backtest(
        self,
        start_date: datetime,
        end_date: datetime,
        system_type: str,
        num_decisions: int = 75,
        enable_rl_learning: bool = True
    ) -> List[DecisionRecord]:
        """
        Run backtest over a date range.
        
        Args:
            start_date: Start date
            end_date: End date
            system_type: System type to test
            num_decisions: Number of decisions to make
            enable_rl_learning: Whether to update RL (only for rl_weights in training)
            
        Returns:
            List of decision records with outcomes
        """
        logger.info(
            f"Starting backtest: {system_type}, {start_date.date()} to {end_date.date()}, "
            f"{num_decisions} decisions, RL learning={'ON' if enable_rl_learning else 'OFF'}"
        )
        
        # Get all trading days in range
        all_data = self.data.df
        mask = (all_data.index >= start_date) & (all_data.index <= end_date)
        trading_days = all_data[mask].index.tolist()
        
        # Filter out dates too close to end (need 7 days forward)
        latest_safe_date = end_date - timedelta(days=10)
        safe_trading_days = [d for d in trading_days if d <= latest_safe_date]
        
        logger.info(f"Found {len(safe_trading_days)} safe trading days")
        
        # Sample random dates
        if len(safe_trading_days) > num_decisions:
            decision_dates = sorted(random.sample(safe_trading_days, num_decisions))
        else:
            decision_dates = sorted(safe_trading_days)
            logger.warning(f"Only {len(decision_dates)} safe dates available")
            
        # Run simulation for each date
        results = []
        correct_count = 0
        
        for i, date in enumerate(decision_dates):
            # Simulate decision
            record = self.simulate_decision(date, system_type)
            
            # Measure outcome
            return_pct, reward = self.measure_outcome(record, date)
            
            # Update record
            record.outcome_7d = return_pct
            record.reward = reward
            record.evaluated = True
            
            # Check if correct
            is_correct = False
            if record.decision == "BUY" and return_pct > 1.0:
                is_correct = True
            elif record.decision == "SELL" and return_pct < -1.0:
                is_correct = True
            elif record.decision == "HOLD" and abs(return_pct) < 2.0:
                is_correct = True
                
            if is_correct:
                correct_count += 1
                
            # Update RL if enabled
            if enable_rl_learning and system_type == 'rl_weights' and self.rl_learner:
                self.rl_learner.update(record, reward)
                
            results.append(record)
            
            if (i + 1) % 25 == 0:
                accuracy = (correct_count / (i + 1)) * 100
                logger.info(f"Progress: {i+1}/{len(decision_dates)} decisions, accuracy={accuracy:.1f}%")
                
        # Final statistics
        accuracy = (correct_count / len(results)) * 100
        avg_reward = np.mean([r.reward for r in results])
        
        logger.info(
            f"Backtest complete: {system_type}, {len(results)} decisions, "
            f"accuracy={accuracy:.1f}%, avg_reward={avg_reward:.3f}"
        )
        
        return results


if __name__ == "__main__":
    # Test backtester
    logging.basicConfig(level=logging.INFO)
    
    from datetime import datetime
    
    # Initialize components
    data = NiftyDataAccessor()
    db = DatabaseManager("backtest.db")
    rl_learner = ThompsonSamplingLearner(db)
    weight_manager = WeightManager(rl_learner=rl_learner)
    
    backtester = Backtester(data, db, weight_manager, rl_learner)
    
    # Test on small range
    test_start = datetime(2025, 2, 1)
    test_end = datetime(2025, 2, 28)
    
    print("Testing backtester on Feb 2025...")
    results = backtester.run_backtest(
        test_start,
        test_end,
        system_type='expert_weights',
        num_decisions=10,
        enable_rl_learning=False
    )
    
    print(f"\nResults: {len(results)} decisions")
    for r in results[:5]:
        print(f"  {r.timestamp[:10]}: {r.decision} → {r.outcome_7d:.2f}%, reward={r.reward:.3f}")
    
    db.close()
