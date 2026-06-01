# Walters Style AFL Player Props Report: Round 12 Current Portfolio

Generated: 2026-05-28 09:48

This card uses the adjusted model line from a simple Kalman-style recent-form update plus mean reversion back toward the season baseline before EV/QI scoring.

## Summary Card

| QI | Signal | Player | Market | Side | Model Line | Market Line | Price | Bookie | EV | Stake |
|---:|---|---|---|---|---:|---:|---:|---|---:|---:|
| 95.0 | A_BET | Shaun Mannagh | Goals | Over | 2.114 | 1.5 | 2.35 | SportsBet | 79.8% | 0.50u |
| 95.0 | A_BET | Liam Fawcett | Goals | Over | 2.129 | 1.5 | 4.20 | SportsBet | 223.5% | 0.50u |
| 95.0 | A_BET | Tom McCarthy | Disposals | Under | 22.304 | 25.5 | 1.87 | PointsBet (AU) | 34.5% | 1.00u |
| 93.5 | A_BET | Toby Greene | Disposals | Over | 20.734 | 17.5 | 1.87 | PointsBet (AU) | 35.0% | 1.00u |
| 93.5 | A_BET | Dion Prestia | Disposals | Under | 17.432 | 22.5 | 1.87 | PointsBet (AU) | 53.6% | 1.00u |
| 93.5 | A_BET | Mason Redman | Disposals | Under | 17.951 | 21.5 | 1.87 | SportsBet | 38.5% | 1.00u |
| 93.5 | A_BET | Archie Roberts | Disposals | Over | 33.667 | 29.5 | 1.87 | PointsBet (AU) | 45.0% | 1.00u |
| 93.5 | A_BET | Kyle Langford | Disposals | Under | 17.148 | 20.5 | 1.87 | PointsBet (AU) | 36.3% | 1.00u |
| 93.5 | A_BET | Sullivan Robey | Disposals | Under | 16.728 | 20.5 | 1.87 | PointsBet (AU) | 40.9% | 1.00u |
| 87.0 | B_BET | Brent Daniels | Goals | Over | 1.565 | 1.5 | 4.00 | TAB | 112.2% | 0.12u |

## Detailed Markov Analysis

Plain-English frame: does the adjusted model support the bet, does the probability still beat the market after smoothing, is the price good enough, and is the confidence high enough to survive Walters-style filtering?

### Shaun Mannagh Goals Over 1.5 @ 2.35 (SportsBet)
- QI: 95.0
- Markov path: Strong -> Dominant -> Mispriced -> Elite
- Average bettor read: the adjusted model line is `2.114` against a market line of `1.5`. The raw season line was `1.727`, and the Kalman/reversion step moved it by `0.387`. That leaves the model showing `76.5%` win probability and `79.8%` EV at `2.35`.
- What it means in plain English: the model still likes this side after smoothing recent form and pulling the player back toward his longer-run baseline, so this is not just a one-hot-game bet.
- Why it made the card: Model data projects 2.114 goals avg against a 1.5 line, creating a +0.6 stat gap for the over. The Markov state path is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price/EV state, and finishes with 95.0 QI. Model probability is 76.5% versus market 42.6%, producing 79.8% EV.
- Ladder context: Over 1.5 @ 2.35 EV 79.8%; Over 0.5 @ 1.27 EV 23.3%
- Main risk: Goals are highest variance; price must compensate for scoring role volatility.

### Liam Fawcett Goals Over 1.5 @ 4.20 (SportsBet)
- QI: 95.0
- Markov path: Strong -> Dominant -> Mispriced -> Elite
- Average bettor read: the adjusted model line is `2.129` against a market line of `1.5`. The raw season line was `2.000`, and the Kalman/reversion step moved it by `0.129`. That leaves the model showing `77.0%` win probability and `223.5%` EV at `4.20`.
- What it means in plain English: the model still likes this side after smoothing recent form and pulling the player back toward his longer-run baseline, so this is not just a one-hot-game bet.
- Why it made the card: Model data projects 2.129 goals avg against a 1.5 line, creating a +0.6 stat gap for the over. The Markov state path is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price/EV state, and finishes with 95.0 QI. Model probability is 77.0% versus market 23.8%, producing 223.5% EV.
- Ladder context: Over 1.5 @ 4.2 EV 223.5%; Over 0.5 @ 1.64 EV 59.5%
- Main risk: Goals are highest variance; price must compensate for scoring role volatility.

### Tom McCarthy Disposals Under 25.5 @ 1.87 (PointsBet (AU))
- QI: 95.0
- Markov path: Strong -> Dominant -> Mispriced -> Elite
- Average bettor read: the adjusted model line is `22.304` against a market line of `25.5`. The raw season line was `22.000`, and the Kalman/reversion step moved it by `0.304`. That leaves the model showing `71.9%` win probability and `34.5%` EV at `1.87`.
- What it means in plain English: the model still likes this side after smoothing recent form and pulling the player back toward his longer-run baseline, so this is not just a one-hot-game bet.
- Why it made the card: Model data projects 22.304 disposals against a 25.5 line, creating a +3.2 stat gap for the under. The Markov state path is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price/EV state, and finishes with 95.0 QI. Model probability is 71.9% versus market 50.0%, producing 34.5% EV.
- Main risk: Disposal props are more stable, but role/rotation drift can still break projection.

### Toby Greene Disposals Over 17.5 @ 1.87 (PointsBet (AU))
- QI: 93.5
- Markov path: Strong -> Dominant -> Mispriced -> Elite
- Average bettor read: the adjusted model line is `20.734` against a market line of `17.5`. The raw season line was `21.636`, and the Kalman/reversion step moved it by `-0.902`. That leaves the model showing `72.2%` win probability and `35.0%` EV at `1.87`.
- What it means in plain English: the model still likes this side after smoothing recent form and pulling the player back toward his longer-run baseline, so this is not just a one-hot-game bet.
- Why it made the card: Model data projects 20.734 disposals against a 17.5 line, creating a +3.2 stat gap for the over. The Markov state path is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price/EV state, and finishes with 93.5 QI. Model probability is 72.2% versus market 50.0%, producing 35.0% EV.
- Main risk: Disposal props are more stable, but role/rotation drift can still break projection.

### Dion Prestia Disposals Under 22.5 @ 1.87 (PointsBet (AU))
- QI: 93.5
- Markov path: Strong -> Dominant -> Mispriced -> Elite
- Average bettor read: the adjusted model line is `17.432` against a market line of `22.5`. The raw season line was `18.286`, and the Kalman/reversion step moved it by `-0.854`. That leaves the model showing `82.2%` win probability and `53.6%` EV at `1.87`.
- What it means in plain English: the model still likes this side after smoothing recent form and pulling the player back toward his longer-run baseline, so this is not just a one-hot-game bet.
- Why it made the card: Model data projects 17.432 disposals against a 22.5 line, creating a +5.1 stat gap for the under. The Markov state path is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price/EV state, and finishes with 93.5 QI. Model probability is 82.2% versus market 50.0%, producing 53.6% EV.
- Main risk: Disposal props are more stable, but role/rotation drift can still break projection.

### Mason Redman Disposals Under 21.5 @ 1.87 (SportsBet)
- QI: 93.5
- Markov path: Strong -> Dominant -> Mispriced -> Elite
- Average bettor read: the adjusted model line is `17.951` against a market line of `21.5`. The raw season line was `17.800`, and the Kalman/reversion step moved it by `0.151`. That leaves the model showing `74.1%` win probability and `38.5%` EV at `1.87`.
- What it means in plain English: the model still likes this side after smoothing recent form and pulling the player back toward his longer-run baseline, so this is not just a one-hot-game bet.
- Why it made the card: Model data projects 17.951 disposals against a 21.5 line, creating a +3.5 stat gap for the under. The Markov state path is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price/EV state, and finishes with 93.5 QI. Model probability is 74.1% versus market 49.9%, producing 38.5% EV.
- Ladder context: Under 21.5 @ 1.87 EV 38.5%; Under 20.5 @ 1.87 EV 26.9%
- Main risk: Disposal props are more stable, but role/rotation drift can still break projection.

### Archie Roberts Disposals Over 29.5 @ 1.87 (PointsBet (AU))
- QI: 93.5
- Markov path: Strong -> Dominant -> Mispriced -> Elite
- Average bettor read: the adjusted model line is `33.667` against a market line of `29.5`. The raw season line was `32.455`, and the Kalman/reversion step moved it by `1.212`. That leaves the model showing `77.6%` win probability and `45.0%` EV at `1.87`.
- What it means in plain English: the model still likes this side after smoothing recent form and pulling the player back toward his longer-run baseline, so this is not just a one-hot-game bet.
- Why it made the card: Model data projects 33.667 disposals against a 29.5 line, creating a +4.2 stat gap for the over. The Markov state path is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price/EV state, and finishes with 93.5 QI. Model probability is 77.6% versus market 50.0%, producing 45.0% EV.
- Main risk: Disposal props are more stable, but role/rotation drift can still break projection.

### Kyle Langford Disposals Under 20.5 @ 1.87 (PointsBet (AU))
- QI: 93.5
- Markov path: Strong -> Dominant -> Mispriced -> Elite
- Average bettor read: the adjusted model line is `17.148` against a market line of `20.5`. The raw season line was `16.727`, and the Kalman/reversion step moved it by `0.421`. That leaves the model showing `72.9%` win probability and `36.3%` EV at `1.87`.
- What it means in plain English: the model still likes this side after smoothing recent form and pulling the player back toward his longer-run baseline, so this is not just a one-hot-game bet.
- Why it made the card: Model data projects 17.148 disposals against a 20.5 line, creating a +3.4 stat gap for the under. The Markov state path is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price/EV state, and finishes with 93.5 QI. Model probability is 72.9% versus market 50.0%, producing 36.3% EV.
- Main risk: Disposal props are more stable, but role/rotation drift can still break projection.

### Sullivan Robey Disposals Under 20.5 @ 1.87 (PointsBet (AU))
- QI: 93.5
- Markov path: Strong -> Dominant -> Mispriced -> Elite
- Average bettor read: the adjusted model line is `16.728` against a market line of `20.5`. The raw season line was `15.857`, and the Kalman/reversion step moved it by `0.871`. That leaves the model showing `75.4%` win probability and `40.9%` EV at `1.87`.
- What it means in plain English: the model still likes this side after smoothing recent form and pulling the player back toward his longer-run baseline, so this is not just a one-hot-game bet.
- Why it made the card: Model data projects 16.728 disposals against a 20.5 line, creating a +3.8 stat gap for the under. The Markov state path is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price/EV state, and finishes with 93.5 QI. Model probability is 75.4% versus market 50.0%, producing 40.9% EV.
- Main risk: Disposal props are more stable, but role/rotation drift can still break projection.

### Brent Daniels Goals Over 1.5 @ 4.00 (TAB)
- QI: 87.0
- Markov path: Lean -> Dominant -> Mispriced -> High
- Average bettor read: the adjusted model line is `1.565` against a market line of `1.5`. The raw season line was `1.667`, and the Kalman/reversion step moved it by `-0.102`. That leaves the model showing `53.0%` win probability and `112.2%` EV at `4.00`.
- What it means in plain English: the model still likes this side after smoothing recent form and pulling the player back toward his longer-run baseline, so this is not just a one-hot-game bet.
- Why it made the card: Model data projects 1.565 goals avg against a 1.5 line, creating a +0.1 stat gap for the over. The Markov state path is Lean -> Dominant -> Mispriced -> High, meaning the row moves from projection support into a positive probability state, then through the price/EV state, and finishes with 87.0 QI. Model probability is 53.0% versus market 25.0%, producing 112.2% EV.
- Ladder context: Over 1.5 @ 4.0 EV 112.2%; Over 0.5 @ 1.6 EV 43.2%
- Main risk: Goals are highest variance; price must compensate for scoring role volatility.
