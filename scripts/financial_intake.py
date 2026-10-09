#!/usr/bin/env python3
"""python scripts/financial_intake.py init|inventory|validate --workspace PATH"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.financial_intake import init_workspace, inventory, save_run, validate


def main():
    parser = argparse.ArgumentParser(description="离线财务原件接收与检查；不猜测 CSMAR 字段")
    parser.add_argument("command", choices=["init", "inventory", "validate"])
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    if args.command == "init":
        print(json.dumps({"workspace": str(args.workspace.resolve()),
                          "created_or_preserved": init_workspace(args.workspace)}, ensure_ascii=False))
    elif args.command == "inventory":
        print(json.dumps(inventory(args.workspace), ensure_ascii=False, indent=2, default=str))
    else:
        if args.input is None:
            parser.error("validate requires --input")
        try:
            rows, report = validate(args.input, args.source_root or args.workspace, args.as_of)
            path = save_run(args.workspace, args.input, rows, report)
        except (ValueError, OSError) as exc:
            parser.exit(2, str(exc) + "\n")
        print(json.dumps({"run": str(path.resolve()), "status": report["status"],
                          "errors": len(report["errors"]), "forecast_updated": False}, ensure_ascii=False))
        return 1 if report["errors"] else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
