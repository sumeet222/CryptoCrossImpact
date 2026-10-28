# Local data contract and rebuild

**Source attribution: Binance Vision.** Dataset terms checked 2026-10-27:
[CC BY-NC-SA 4.0 and supplemental dataset terms](https://github.com/binance/binance-public-data/blob/master/TERMS_AND_CONDITIONS.md).
Derived data/QA summaries are subject to the same attribution, noncommercial and
share-alike terms. No raw vendor data are included in Git.

Official source:
`https://data.binance.vision/data/futures/um/monthly/klines/{SYMBOL}/1m/{SYMBOL}-1m-{YYYY-MM}.zip`
plus `.CHECKSUM`. Both BTCUSDT and ETHUSDT **USDT-margined perpetual last-trade**
klines, January 2024–June 2026 inclusive: 60 symbol-months. Never substitute spot,
COIN-M, mark/index price, another venue or fabricated bars. Schema documentation:
https://github.com/binance/binance-public-data .

`raw/` retains one verified compressed monthly source plus checksum. `canonical/`
retains one Zstandard Parquet per symbol-month; `tmp/` is reserved for this
operation's temporary files. All are ignored. `registry/` holds small trackable
source IDs/hashes, exact missing spans, exclusion counts and run provenance.

Vendor fields are kept as integer millisecond timestamps/integer trade count and
float64 price/volume data. Base units are BTC or ETH, quote units USDT. Additional
columns:

| Column | Meaning / availability |
|---|---|
| `symbol` | Exact source contract |
| `bar_open_utc`, `bar_close_utc` | UTC vendor open and open+59,999 ms |
| `available_at_utc` | Conservative full-bar availability: open+60,000 ms |
| `split` | Fixed UTC **bar-open calendar** train/validation/test mask |
| `buy_quote_volume`, `sell_quote_volume` | Taker-buy and total minus buy, USDT |
| `signed_taker_quote_flow` | `2*buy-total`, USDT, aggressive buyer positive |
| `signed_taker_flow_ratio` | Signed/total; undefined at zero turnover |
| `log_close` | Natural log of positive recorded close |
| `close_to_close_log_return` | Dimensionless log return, consecutive valid bars only |
| `quality_bits`, `valid_bar` | Row validity and explicit anomaly reason bits |
| `valid_return` | Current and predecessor valid and exactly one minute apart |
| `jump_flag`, `stale_close_flag` | Fixed QC diagnostics, no automatic exclusions |

Quality bits: 1 nonfinite; 2 invalid OHLC; 4 negative volume/count; 8 taker exceeds
total; 16 inconsistent volume/trade-count/notional. Comparisons use 1e-8 absolute
plus 1e-12 relative rounding allowance, without altering source values. No missing
bars or invalid values are imputed. An entire regression lag window must be valid
in Stage 2; Stage 1's valid-bar/return counts are **not** lag-window eligibility.
Observed zero turnover preserves recorded price and zero signed flow; the ratio
is undefined. Final sample bar belongs to test though available at 2026-07-01.

Rebuild from the root using the `preflight`, `pilot`, `acquire`, `audit`, `qc`
commands in [README](../README.md). There is no test split copy. Inspect
`registry/qc_summary.json` and [quality report](../reports/data/stage01_data_quality.md)
before later estimation. No Stage 2 normalization or fitting has been performed.
