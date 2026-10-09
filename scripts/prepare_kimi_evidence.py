"""Validate a Kimi candidate return and prepare a separate offline review batch."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.kimi_intake import prepare_candidates

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--source-root', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    try:
        result = prepare_candidates(a.input, a.source_root, a.out)
    except (ValueError, OSError) as exc:
        p.exit(2, str(exc) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
