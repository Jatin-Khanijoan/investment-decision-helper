"""
Reward calculator for RL-based decision system.
Calculates rewards from decisions and their outcomes.
"""
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def calculate_reward(
    decision: str,
    price_at_decision: float,
    price_after_7d: float,
    confidence: float
) -> Tuple[float, dict]:
    """
    Calculate reward for a decision based on outcomes.
    
    Args:
        decision: "BUY", "HOLD", or "SELL"
        price_at_decision: Price when decision was made
        price_after_7d: Price 7 trading days later
        confidence: Confidence level of decision (0-1)
        
    Returns:
        Tuple of (total_reward, breakdown_dict)
        
    Reward components:
    1. Directional accuracy: BUY+up=+1.0, SELL+down=+1.0, HOLD+stable=+0.5, wrong=-0.5
    2. Confidence calibration: confident+correct=+0.2, confident+wrong=-0.3
    3. Magnitude bonus: scaled by return percentage
    
    Total range: approximately -0.8 to +1.7
    """
    # Calculate return percentage
    if price_at_decision == 0:
        logger.error("Invalid price_at_decision: 0")
        return 0.0, {}
        
    return_pct = ((price_after_7d - price_at_decision) / price_at_decision) * 100
    
    # Component 1: Directional accuracy
    directional_reward = 0.0
    is_correct = False
    
    if decision == "BUY":
        if return_pct > 1.0:  # Price went up at least 1%
            directional_reward = 1.0
            is_correct = True
        elif return_pct < -1.0:  # Price went down
            directional_reward = -0.5
        else:  # Neutral
            directional_reward = 0.0
            
    elif decision == "SELL":
        if return_pct < -1.0:  # Price went down
            directional_reward = 1.0
            is_correct = True
        elif return_pct > 1.0:  # Price went up
            directional_reward = -0.5
        else:  # Neutral
            directional_reward = 0.0
            
    elif decision == "HOLD":
        if abs(return_pct) < 2.0:  # Price stayed relatively stable
            directional_reward = 0.5
            is_correct = True
        else:  # Large move (should have been BUY or SELL)
            directional_reward = -0.2
    else:
        logger.warning(f"Unknown decision: {decision}")
        directional_reward = 0.0
        
    # Component 2: Confidence calibration
    # Reward well-calibrated confidence, penalize overconfidence
    confidence_reward = 0.0
    
    if is_correct:
        # Correct decision - reward higher confidence
        if confidence > 0.7:
            confidence_reward = 0.2
        elif confidence > 0.5:
            confidence_reward = 0.1
        else:
            confidence_reward = 0.0
    else:
        # Incorrect decision - penalize high confidence
        if confidence > 0.7:
            confidence_reward = -0.3
        elif confidence > 0.5:
            confidence_reward = -0.15
        else:
            confidence_reward = 0.0  # Low confidence, no penalty
            
    # Component 3: Magnitude bonus
    # Scale reward by the magnitude of the return
    magnitude_bonus = 0.0
    
    if is_correct:
        # Bonus for larger correct moves
        magnitude_bonus = min(0.5, abs(return_pct) / 20.0)  # Cap at 0.5
    
    # Calculate total reward
    total_reward = directional_reward + confidence_reward + magnitude_bonus
    
    # Create breakdown for logging/analysis
    breakdown = {
        "return_pct": return_pct,
        "directional_reward": directional_reward,
        "confidence_reward": confidence_reward,
        "magnitude_bonus": magnitude_bonus,
        "total_reward": total_reward,
        "is_correct": is_correct,
    }
    
    logger.info(
        f"Reward: {total_reward:.3f} for {decision} "
        f"(return={return_pct:.2f}%, conf={confidence:.2f}, correct={is_correct})"
    )
    logger.debug(f"Breakdown: {breakdown}")
    
    return total_reward, breakdown


if __name__ == "__main__":
    # Test reward calculations
    logging.basicConfig(level=logging.INFO)
    
    test_cases = [
        ("BUY", 100.0, 110.0, 0.8, "Correct BUY, high confidence"),
        ("BUY", 100.0, 95.0, 0.8, "Incorrect BUY, high confidence"),
        ("SELL", 100.0, 95.0, 0.7, "Correct SELL, medium confidence"),
        ("HOLD", 100.0, 101.0, 0.6, "Correct HOLD, stable price"),
        ("BUY", 100.0, 112.0, 0.9, "Correct BUY, large move"),
        ("BUY", 100.0, 98.0, 0.4, "Incorrect BUY, low confidence"),
    ]
    
    print("Reward Calculation Tests:\n")
    for decision, price_at, price_after, conf, description in test_cases:
        reward, breakdown = calculate_reward(decision, price_at, price_after, conf)
        print(f"{description}:")
        print(f"  Decision: {decision}, Return: {breakdown['return_pct']:.2f}%")
        print(f"  Reward breakdown:")
        print(f"    Directional: {breakdown['directional_reward']:.2f}")
        print(f"    Confidence: {breakdown['confidence_reward']:.2f}")
        print(f"    Magnitude: {breakdown['magnitude_bonus']:.2f}")
        print(f"    TOTAL: {breakdown['total_reward']:.2f}")
        print()
