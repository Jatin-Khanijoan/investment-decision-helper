#!/usr/bin/env python3
from data_accessor import NiftyDataAccessor
from datetime import datetime

accessor = NiftyDataAccessor()

# Test getting a 7-day outcome
test_date = datetime(2025, 6, 2)
price_at = accessor.get_price(test_date, 'Close')
price_after = accessor.get_price_after_days(test_date, days_ahead=7)

if price_at and price_after:
    return_pct = ((price_after - price_at) / price_at) * 100
    print(f"Date: {test_date.date()}")
    print(f"Price at decision: {price_at:.2f}")
    print(f"Price after 7 days: {price_after:.2f}")
    print(f"Return: {return_pct:.2f}%")
    
    from reward_calculator import calculate_reward
    reward, breakdown = calculate_reward("BUY", price_at, price_after, 0.8)
    print(f"\nReward for BUY decision: {reward:.3f}")
    print(f"Breakdown: {breakdown}")
else:
    print("Could not get prices (weekend/holiday)")
