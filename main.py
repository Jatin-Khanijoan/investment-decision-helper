#!/usr/bin/env python3
import sys
import json
import asyncio
import argparse
import logging
from providers.utils import load_universe, validate_symbol
from graph import build_graph
from state import DecisionState

# Configure logging
import os

log_file = os.path.join(os.path.dirname(__file__), "kautilya.log")

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create formatters
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# Create handlers
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Also configure root logger to capture all other log messages
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)


async def main():
    logger.info("Starting NIFTY50 Investment Decision Helper")

    parser = argparse.ArgumentParser(description="NIFTY50 Investment Decision Helper")
    parser.add_argument("--user_id", required=True, help="User ID")
    parser.add_argument("--question", required=True, help="Investment question")
    parser.add_argument("--symbol", required=True, help="NIFTY50 symbol")
    parser.add_argument("--sector", help="Sector (optional)")

    args = parser.parse_args()

    logger.info(
        "Processing request: user=%s, symbol=%s, question='%s'",
        args.user_id,
        args.symbol,
        args.question[:50],
    )

    # Validate symbol
    universe = load_universe("stocks.json")
    if not validate_symbol(args.symbol, universe):
        logger.error("Invalid symbol: %s not in NIFTY50 universe", args.symbol)
        print(f"Error: {args.symbol} not in NIFTY50 universe", file=sys.stderr)
        sys.exit(2)

    # Build initial state
    initial_state: DecisionState = {
        "user_id": args.user_id,
        "question": args.question,
        "symbol": args.symbol,
        "sector": args.sector,
        "agent_outputs": {},
        "citations": [],
        "errors": [],
    }

    logger.info("Building and executing LangGraph workflow")
    # Run graph
    graph = build_graph()
    result = await graph.ainvoke(initial_state)

    # Output decision JSON
    if "decision_json" in result:
        logger.info("Decision completed successfully")
        print(json.dumps(result["decision_json"], indent=2))
    else:
        logger.error("No decision_json found in result")
        # Provide conservative HOLD decision
        print(
            json.dumps(
                {
                    "decision": "HOLD",
                    "confidence": 0.1,
                    "horizon": "medium",
                    "why": "System error: Failed to generate decision. HOLD recommended as conservative default.",
                    "key_factors": ["System processing error"],
                    "risks": ["Unable to complete analysis"],
                    "personalization_considerations": ["Conservative approach advised"],
                    "used_agents": [],
                    "citations": [],
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
