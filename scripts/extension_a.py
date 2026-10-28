#!/usr/bin/env python3
"""Stage A ordered, checkpointed scientific gates."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))

def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['math','features','fit','pilot','development','report','confirmation','all']);a=p.parse_args();root=Path(__file__).resolve().parents[1]
    from cryptocrossimpact.stage_a.runner import run
    run(root,a.command)
if __name__=='__main__':main()
