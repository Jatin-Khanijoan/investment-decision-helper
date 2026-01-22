#!/bin/bash

# Example usage of NIFTY50 Investment Decision Helper
# The system will always provide BUY/HOLD/SELL decisions, never INSUFFICIENT_DATA

# Set API keys (required for actual functionality)
# export GEMINI_API_KEY="your-gemini-api-key-here"
# export GEMINI_MODEL="gemini-2.0-flash-thinking-exp-1219"
# export TAVILY_API_KEY="your-tavily-api-key-here"
# export RETURN_REASONING=true

echo "Example 1: Query for RELIANCE"
python main.py \
  --user_id U123 \
  --question "Should I increase allocation to RELIANCE for the next 6 months?" \
  --symbol RELIANCE \
  --sector Energy

echo ""
echo "Example 2: Query for TCS"
python main.py \
  --user_id U456 \
  --question "Is TCS a good buy for long-term investment?" \
  --symbol TCS \
  --sector IT

echo ""
echo "Example 3: Query for HDFCBANK"
python main.py \
  --user_id U789 \
  --question "Should I hold or sell HDFC Bank given current interest rates?" \
  --symbol HDFCBANK \
  --sector Banking
