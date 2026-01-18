from __future__ import annotations

import argparse
import logging
from pathlib import Path

from agent.loop import DEFAULT_INPUT_PATH, DEFAULT_POLL_INTERVAL_SEC, run_loop


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the SpaceTraders agent loop")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH, help="Path to advisory input file")
    parser.add_argument("--poll-interval", type=float, default=DEFAULT_POLL_INTERVAL_SEC, help="Polling interval seconds")
    parser.add_argument("--once", action="store_true", help="Run a single iteration and exit")
    parser.add_argument("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR)")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    logger = logging.getLogger("agent")
    logger.info("Starting agent (once=%s, poll=%.2fs, input=%s)", args.once, args.poll_interval, args.input)
    run_loop(input_path=args.input, poll_interval_sec=args.poll_interval, once=args.once, logger=logger)


if __name__ == "__main__":
    main()
