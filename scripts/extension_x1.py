#!/usr/bin/env python3
"""X1 development-only forecast, pilot, replay and report entrypoint."""
from pathlib import Path
import argparse
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from cryptocrossimpact.liquidity.workflow import forecasts,development,preservation


def main():
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['forecasts','pilot','development','report','preserve'])
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    if args.command=='forecasts':forecasts(root)
    elif args.command=='pilot':development(root,True)
    elif args.command=='development':development(root)
    elif args.command=='preserve':print(preservation(root,True))
    else:
        from cryptocrossimpact.liquidity.reporting import report
        report(root)
if __name__=='__main__':main()
