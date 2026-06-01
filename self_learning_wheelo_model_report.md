# Self-Learning Wheelo AFL Prop Model

Method:
- Input: direct WheeloRatings.com player stats joined to BetMate lines.
- Truth: Footywire-settled `final_stat`.
- Training: first three chronological match dates.
- Holdout: final chronological match date.
- Learner: market-specific threshold search over QI, model edge, support level, and price band.
- Excluded: ranking/fantasy points until they can be priced separately.

## Learned Rules

| Market | Support | Min QI | Min Edge | Price Band | Train Bets | Train ROI |
|---|---|---:|---:|---|---:|---:|
| Disposals | strong | 55 | 0.20 | 1.01-10.00 | 42 | 1.5% |
| Goals | strong | 85 | -0.02 | 1.60-2.40 | 42 | 1.6% |
| Tackles | strong | 55 | 0.08 | 1.01-10.00 | 18 | 3.7% |

## Performance

| Split | Bets | Hit Rate | Profit | ROI |
|---|---:|---:|---:|---:|
| Train selected | 102 | 94.1% | $63.33 | 1.8% |
| Holdout selected | 45 | 46.7% | $-1.29 | -0.1% |
| Expanding walk-forward selected | 189 | 66.7% | $24.72 | 0.4% |
| All selected | 147 | 79.6% | $62.04 | 1.2% |
| All available approved markets | 4354 | 52.5% | $67.01 | 0.0% |

## Expanding Walk-Forward Audit

| Test Date | Prior Train Dates | Rules | Bets | Hit Rate | Profit | ROI |
|---|---|---:|---:|---:|---:|---:|
| 2026-03-06 | 2026-03-05 | 3 | 90 | 66.7% | $7.80 | 0.2% |
| 2026-03-07 | 2026-03-05, 2026-03-06 | 3 | 54 | 83.3% | $18.21 | 1.0% |
| 2026-03-08 | 2026-03-05, 2026-03-06, 2026-03-07 | 3 | 45 | 46.7% | $-1.29 | -0.1% |

## Holdout By Market

| Market | Bets | Hit Rate | Profit | ROI |
|---|---:|---:|---:|---:|
| Goals | 36 | 33.3% | $-3.84 | -0.3% |
| Tackles | 9 | 100.0% | $2.55 | 0.5% |

## Interpretation

This is the sharpest current version because it learns market-specific gates from prior settled rows, then tests them chronologically out-of-sample. It still needs prop CLV and timestamped pre-bounce Wheelo snapshots for an institutional-grade proof.
