# WheeloRatings + Footywire AFL Prop Backtest

Source contract:
- Model input: WheeloRatings.com player season, Last5, Last10 data.
- Settlement truth: Footywire final player stat written into `final_stat`.
- Market input: BetMate captured line, price, book, QI, and stake.

Wheelo source URLs:
- Season: https://www.wheeloratings.com/src/afl_stats/player_stats/afl/2026.json
- Last5: https://www.wheeloratings.com/src/afl_stats/player_stats/afl/last5.json
- Last10: https://www.wheeloratings.com/src/afl_stats/player_stats/afl/last10.json

Loaded Wheelo snapshots:
- Season: `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/wheelo_live_2026.json`
- Last5: `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/wheelo_live_last5.json`
- Last10: `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/wheelo_live_last10.json`

Wheelo metadata:
- Season latest games: 23 May 2026: North Melbourne v Gold Coast, Geelong v Sydney, Collingwood v West Coast, Port Adelaide v Carlton (Round 11)
- Last5 latest games: 23 May 2026: North Melbourne v Gold Coast, Geelong v Sydney, Collingwood v West Coast, Port Adelaide v Carlton (Round 11)
- Last10 latest games: 23 May 2026: North Melbourne v Gold Coast, Geelong v Sydney, Collingwood v West Coast, Port Adelaide v Carlton (Round 11)

Status: replay diagnostic, not pure timestamped walk-forward. Full walk-forward requires archived Wheelo snapshots for each `captured_datetime`.

## Overall

| Bets | Hit Rate | Profit | ROI |
|---:|---:|---:|---:|
| 5113 | 52.8% | $67.01 | 22.6% |

## Decision Rules

| Rule | Bets | Hit Rate | Profit | ROI |
|---|---:|---:|---:|---:|
| Model QI >= 70 + model lean/strong support | 1252 | 72.7% | $67.01 | 22.6% |
| Model QI >= 80 + model strong support | 590 | 76.8% | $70.68 | 27.9% |
| A_BET: approved market + model QI>=80 + strong model support + edge>=4% | 345 | 75.7% | $70.74 | 28.3% |
| A/B_BET: approved market + model QI>=70 + model support + edge | 442 | 71.9% | $67.01 | 22.6% |

### By Model Support

| Segment | Bets | Hit Rate | Profit | ROI |
|---|---:|---:|---:|---:|
| Model strong support | 1768 | 76.2% | $69.87 | 25.9% |
| Model neutral | 899 | 53.9% | $0.00 | 0.0% |
| Model strong against | 873 | 28.9% | $0.00 | 0.0% |
| Model lean against | 685 | 25.7% | $0.00 | 0.0% |
| No Model data match | 111 | 40.5% | $0.00 | 0.0% |
| Model lean support | 777 | 51.1% | $-2.86 | -10.4% |

### By Market

| Segment | Bets | Hit Rate | Profit | ROI |
|---|---:|---:|---:|---:|
| Tackles | 960 | 46.5% | $22.13 | 82.6% |
| Goals | 1625 | 46.5% | $22.26 | 41.2% |
| Disposals | 1350 | 67.3% | $22.62 | 10.5% |
| Ranking/Fantasy Pts | 666 | 57.4% | $0.00 | 0.0% |
| Marks | 512 | 41.0% | $0.00 | 0.0% |

### By New Bet Rule

| Segment | Bets | Hit Rate | Profit | ROI |
|---|---:|---:|---:|---:|
| A_BET | 345 | 75.7% | $70.74 | 28.3% |
| PASS | 3487 | 48.9% | $0.00 | 0.0% |
| PASS_EXCLUDED_MARKET | 666 | 57.4% | $0.00 | 0.0% |
| LEAN | 425 | 62.1% | $0.00 | 0.0% |
| PASS_NO_MODEL | 93 | 35.5% | $0.00 | 0.0% |
| B_BET | 97 | 58.8% | $-3.73 | -7.9% |

### Market x Model Support

| Segment | Bets | Hit Rate | Profit | ROI |
|---|---:|---:|---:|---:|
| Tackles | Model strong support | 141 | 59.6% | $22.53 | 85.3% |
| Goals | Model strong support | 600 | 70.0% | $22.26 | 41.2% |
| Disposals | Model strong support | 555 | 88.1% | $25.08 | 13.3% |
| Goals | Model strong against | 377 | 33.7% | $0.00 | 0.0% |
| Ranking/Fantasy Pts | Model strong support | 314 | 79.0% | $0.00 | 0.0% |
| Tackles | Model neutral | 290 | 57.9% | $0.00 | 0.0% |
| Goals | Model lean against | 276 | 23.2% | $0.00 | 0.0% |
| Tackles | Model strong against | 267 | 33.7% | $0.00 | 0.0% |
| Disposals | Model neutral | 264 | 54.5% | $0.00 | 0.0% |
| Goals | Model lean support | 204 | 41.2% | $0.00 | 0.0% |
| Disposals | Model lean against | 165 | 36.4% | $0.00 | 0.0% |
| Marks | Model strong support | 158 | 67.1% | $0.00 | 0.0% |
| Tackles | Model lean against | 151 | 23.8% | $0.00 | 0.0% |
| Marks | Model neutral | 126 | 40.5% | $0.00 | 0.0% |
| Goals | Model neutral | 120 | 45.0% | $0.00 | 0.0% |
| Ranking/Fantasy Pts | Model lean support | 99 | 32.3% | $0.00 | 0.0% |
| Ranking/Fantasy Pts | Model neutral | 99 | 68.7% | $0.00 | 0.0% |
| Marks | Model lean support | 96 | 37.5% | $0.00 | 0.0% |
| Marks | Model strong against | 88 | 8.0% | $0.00 | 0.0% |
| Ranking/Fantasy Pts | Model strong against | 81 | 12.3% | $0.00 | 0.0% |
| Disposals | Model strong against | 60 | 30.0% | $0.00 | 0.0% |
| Ranking/Fantasy Pts | Model lean against | 55 | 21.8% | $0.00 | 0.0% |
| Disposals | Model lean support | 276 | 65.2% | $-2.46 | -9.1% |
| Tackles | Model lean support | 102 | 63.7% | $-0.40 | -100.0% |

### Market x New Bet Rule

| Segment | Bets | Hit Rate | Profit | ROI |
|---|---:|---:|---:|---:|
| Tackles | A_BET | 27 | 100.0% | $22.02 | 101.9% |
| Goals | A_BET | 144 | 66.7% | $22.26 | 41.2% |
| Disposals | A_BET | 174 | 79.3% | $26.46 | 15.2% |
| Goals | PASS | 1223 | 41.6% | $0.00 | 0.0% |
| Disposals | PASS | 1014 | 67.2% | $0.00 | 0.0% |
| Tackles | PASS | 908 | 44.5% | $0.00 | 0.0% |
| Ranking/Fantasy Pts | PASS_EXCLUDED_MARKET | 666 | 57.4% | $0.00 | 0.0% |
| Marks | PASS | 342 | 32.5% | $0.00 | 0.0% |
| Goals | LEAN | 210 | 68.6% | $0.00 | 0.0% |
| Marks | LEAN | 164 | 56.7% | $0.00 | 0.0% |
| Disposals | LEAN | 48 | 50.0% | $0.00 | 0.0% |
| Goals | PASS_NO_MODEL | 48 | 12.5% | $0.00 | 0.0% |
| Disposals | PASS_NO_MODEL | 30 | 60.0% | $0.00 | 0.0% |
| Disposals | B_BET | 84 | 57.1% | $-3.84 | -9.1% |

### Model Support x Model QI Tier

| Segment | Bets | Hit Rate | Profit | ROI |
|---|---:|---:|---:|---:|
| Model strong support | QI 90+ | 153 | 76.5% | $55.95 | 49.1% |
| Model strong support | QI 80-89 | 437 | 76.9% | $14.73 | 10.6% |
| Model strong against | QI <60 | 873 | 28.9% | $0.00 | 0.0% |
| Model neutral | QI <60 | 829 | 56.3% | $0.00 | 0.0% |
| Model lean against | QI <60 | 685 | 25.7% | $0.00 | 0.0% |
| Model lean support | QI <60 | 463 | 54.6% | $0.00 | 0.0% |
| Model strong support | QI 60-69 | 339 | 77.0% | $0.00 | 0.0% |
| Model strong support | QI <60 | 321 | 76.6% | $0.00 | 0.0% |
| Model lean support | QI 60-69 | 170 | 43.5% | $0.00 | 0.0% |
| No Model data match | QI <60 | 111 | 40.5% | $0.00 | 0.0% |
| Model neutral | QI 60-69 | 70 | 25.7% | $0.00 | 0.0% |
| Model strong support | QI 70-79 | 518 | 74.7% | $-0.81 | -5.0% |
| Model lean support | QI 70-79 | 113 | 51.3% | $-3.84 | -25.6% |

### Market x Book

| Segment | Bets | Hit Rate | Profit | ROI |
|---|---:|---:|---:|---:|
| Tackles | PointsBet (AU) | 30 | 80.0% | $8.88 | 185.0% |
| Goals | Dabble AU | 138 | 47.8% | $10.32 | 114.7% |
| Disposals | Unibet | 42 | 71.4% | $3.30 | 110.0% |
| Tackles | SportsBet | 495 | 47.5% | $10.77 | 74.8% |
| Goals | TAB | 210 | 40.0% | $4.92 | 54.7% |
| Disposals | SportsBet | 54 | 22.2% | $2.88 | 48.0% |
| Tackles | Unibet | 315 | 46.7% | $2.88 | 40.0% |
| Goals | PointsBet (AU) | 603 | 57.4% | $10.56 | 39.1% |
| Disposals | Dabble AU | 594 | 69.7% | $33.30 | 21.3% |
| Disposals | Neds | 336 | 80.4% | $0.18 | 6.0% |
| Ranking/Fantasy Pts | Neds | 636 | 58.5% | $0.00 | 0.0% |
| Marks | SportsBet | 340 | 42.4% | $0.00 | 0.0% |
| Goals | Bet Right | 299 | 30.4% | $0.00 | 0.0% |
| Marks | PointsBet (AU) | 96 | 53.1% | $0.00 | 0.0% |
| Marks | TAB | 67 | 13.4% | $0.00 | 0.0% |
| Disposals | TAB | 300 | 58.0% | $-17.04 | -35.5% |
| Goals | Betr | 225 | 48.0% | $-2.04 | -45.3% |
| Goals | Neds | 132 | 31.8% | $-1.50 | -100.0% |
| Tackles | TAB | 104 | 23.1% | $-0.40 | -100.0% |
