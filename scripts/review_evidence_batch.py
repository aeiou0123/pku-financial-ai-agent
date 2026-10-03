"""Review a UTF-8 CSV batch into a fresh output directory, without API keys."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.evidence_batch import review_batch

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    try:result=review_batch(args.input,args.out)
    except (ValueError,OSError) as exc:parser.exit(2,str(exc)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    sys.exit(1 if result['invalid_input'] else 0)
