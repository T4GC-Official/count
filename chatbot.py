"""Main entry point for the Telegram bot system with plugin support."""

import argparse
import importlib
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    parser = argparse.ArgumentParser(
        description="Telegram Bot with Plugin Support")
    parser.add_argument("--plugin", type=str, default="om",
                        help="Plugin to use (om/lipok)")
    parser.add_argument("--host", type=str, default="127.0.0.1",
                        help="The MongoDB host/container name")
    parser.add_argument("--port", type=str, default="27017",
                        help="The MongoDB port")
    parser.add_argument("--bot_name", type=str, default="ari",
                        help="User supplied chatbot name - this namespaces the database so you can run multiple bots on the same server and they will use different tables. It has no relationship to the bot name in telegram.")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level"
    )

    # Set the global logging level, which base.py inherits when it creates a
    # logger for the plugin.
    args = parser.parse_args()
    logging.getLogger().setLevel(args.log_level)

    api_key = os.getenv('API_KEY')
    if not api_key:
        raise ValueError("API_KEY env var is not set.")

    # Import and run the specified plugin
    try:
        plugin_module = importlib.import_module(f"bots.{args.plugin}")
        plugin_module.run_bot(api_key=api_key, **vars(args))
    except ImportError:
        raise ValueError(f"Plugin '{args.plugin}' not found in bots directory")


if __name__ == '__main__':
    main()
