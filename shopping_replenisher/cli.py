"""CLI entry points for the shopping replenisher."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from shopping_replenisher.config import AppConfig, ConfigError, load_config


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""

    parser = argparse.ArgumentParser(prog="shopping-replenisher")
    parser.add_argument(
        "--dotenv-path",
        type=Path,
        default=None,
        help="Optional path to a .env file.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("inspect", help="Validate configuration and print a summary.")

    predict_parser = subparsers.add_parser("predict", help="Stub for local prediction flow.")
    predict_parser.add_argument(
        "--json",
        action="store_true",
        help="Reserved flag for JSON output.",
    )

    run_parser = subparsers.add_parser("run", help="Stub for the end-to-end pipeline.")
    run_parser.add_argument(
        "--apply",
        action="store_true",
        help="Reserved flag for apply mode.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the shopping replenisher CLI."""

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_config(args.dotenv_path)
    except ConfigError as exc:
        parser.exit(status=2, message=f"Configuration error: {exc}\n")

    if args.command == "inspect":
        return _handle_inspect(config)
    if args.command == "predict":
        return _handle_predict(config, output_json=args.json)
    if args.command == "run":
        return _handle_run(config, apply_mode=args.apply)

    parser.exit(status=2, message=f"Unknown command: {args.command}\n")
    return 2


def _handle_inspect(config: AppConfig) -> int:
    """Handle the inspect subcommand."""

    print("Configuration is valid.")
    print(f"TODOIST_DB_PATH={config.todoist_db_path}")
    print(f"SHOPPING_PROJECT_ID={config.shopping_project_id}")
    print(f"AUTO_APPLY={config.auto_apply}")
    print(f"LOG_LEVEL={config.log_level}")
    return 0


def _handle_predict(config: AppConfig, output_json: bool) -> int:
    """Handle the predict subcommand stub."""

    _ = config
    _ = output_json
    print("The 'predict' command is not implemented yet.")
    return 0


def _handle_run(config: AppConfig, apply_mode: bool) -> int:
    """Handle the run subcommand stub."""

    _ = config
    _ = apply_mode
    print("The 'run' command is not implemented yet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

