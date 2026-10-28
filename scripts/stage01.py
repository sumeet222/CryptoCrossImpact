"""Thin repo-root entry point; no editable install required."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cryptocrossimpact.data.pipeline import main

if __name__ == "__main__":
    main()
