"""Inspect all development jump/stale flagged days; test economic plots excluded."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "data/tmp/matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def main():
    records = pd.read_csv(ROOT / "data/registry/qc_anomalies.csv")
    for (symbol, month), group in records.loc[records.split != "test"].groupby(["symbol", "month"]):
        bars = pd.read_parquet(ROOT / "data/canonical" / symbol / f"{month}.parquet")
        dates = sorted(set(group.first_open_utc.str[:10]) | set(group.last_open_utc.str[:10]))
        for date in dates:
            day = bars.loc[bars.bar_open_utc.dt.strftime("%Y-%m-%d") == date]
            fig, axes = plt.subplots(2, 1, figsize=(9, 4.8), sharex=True, constrained_layout=True)
            axes[0].plot(day.bar_open_utc, day.close, linewidth=.9)
            flagged = day.jump_flag | day.stale_close_flag
            axes[0].scatter(day.loc[flagged, "bar_open_utc"], day.loc[flagged, "close"], s=10, color="crimson", label="fixed QC flags")
            axes[0].set_ylabel("Close (USDT/base token)")
            axes[0].legend(loc="best", fontsize=8)
            axes[0].set_title(f"{symbol} USD-M perpetual — {date} — source QC only")
            axes[1].plot(day.bar_open_utc, day.quote_volume / 1e6, linewidth=.7)
            zero = day.quote_volume == 0
            axes[1].scatter(day.loc[zero, "bar_open_utc"], day.loc[zero, "quote_volume"], s=12, color="orange", label="reported zero turnover")
            axes[1].set_ylabel("1m turnover (million USDT)")
            axes[1].set_xlabel("Bar open (UTC)")
            axes[1].legend(loc="best", fontsize=8)
            path = ROOT / "reports/data" / f"stage01_qc_{symbol}_{date}.png"
            fig.savefig(path, dpi=110)
            plt.close(fig)
            print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
