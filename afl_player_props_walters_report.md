# Walters Style AFL Player Props Report: Round 12 Current Portfolio

Generated: 2026-05-30 21:03

This card uses the adjusted model line from a simple Kalman-style recent-form update plus mean reversion back toward the season baseline before EV/QI scoring.

## Summary Card

| QI | Signal | Player | Market | Side | Model Line | Market Line | Price | Bookie | EV | Stake |
|---:|---|---|---|---|---:|---:|---:|---|---:|---:|
| 95.0 | A_BET | Toby Greene | Disposals | Over | 20.734 | 17.5 | 1.90 | SportsBet | 33.4% | 1.00u |
| 95.0 | A_BET | Paddy Cross | Goals | Over | 1.000 | 0.5 | 2.60 | PointsBet (AU) | 64.4% | 0.50u |
| 95.0 | A_BET | Tom McCarthy | Disposals | Under | 22.304 | 25.5 | 1.89 | SportsBet | 34.9% | 1.00u |
| 93.5 | A_BET | Conor Stone | Disposals | Over | 22.000 | 17.5 | 1.94 | SportsBet | 49.4% | 1.00u |
| 93.5 | A_BET | Archie Roberts | Disposals | Over | 33.667 | 29.5 | 1.87 | PointsBet (AU) | 40.4% | 1.00u |
| 93.5 | A_BET | Kyle Langford | Disposals | Under | 17.148 | 20.5 | 1.87 | PointsBet (AU) | 34.9% | 1.00u |
| 93.5 | A_BET | Sullivan Robey | Disposals | Under | 16.728 | 20.5 | 1.87 | PointsBet (AU) | 36.0% | 1.00u |
| 93.0 | A_BET | Leek Aleer | Tackles | Over | 4.606 | 3.5 | 2.90 | PointsBet (AU) | 83.1% | 0.80u |
| 92.0 | A_BET | Andy Moniz-Wakefield | Goals | Over | 1.000 | 0.5 | 2.45 | Betr | 54.9% | 0.50u |
| 92.0 | A_BET | Will Setterfield | Goals | Over | 1.000 | 0.5 | 3.15 | Bet Right | 99.1% | 0.50u |

## Detailed Markov Analysis

Plain-English frame: does the adjusted model support the bet, does the probability still beat the market after smoothing, is the price good enough, and is the confidence high enough to survive Walters-style filtering?

### Toby Greene Disposals Over 17.5 @ 1.90 (SportsBet)
- QI: 95.0
- Markov path: Strong -> Dominant -> Mispriced -> Elite
- Average bettor read: the adjusted model line is `20.734` against a market line of `17.5`. The raw season line was `21.636`, and the Kalman/reversion step moved it by `-0.902`. That leaves the model showing `70.2%` win probability and `33.4%` EV at `1.90`.
- What it means in plain English: the model still likes this side after smoothing recent form and pulling the player back toward his longer-run baseline, so this is not just a one-hot-game bet.
- Why it made the card: Model data projects 20.734 disposals against a 17.5 line, creating a +3.2 stat gap for the over. The Markov state path is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price/EV state, and finishes with 95.0 QI. Model probability is 70.2% versus market 49.1%, producing 33.4% EV.
- Main risk: Disposal props are more stable, but role/rotation drift can still break projection.

### Paddy Cross Goals Over 0.5 @ 2.60 (PointsBet (AU))
- QI: 95.0
- Markov path: Strong -> Dominant -> Mispriced -> Elite
- Average bettor read: the adjusted model line is `1.000` against a market line of `0.5`. The raw season line was `1.000`, and the Kalman/reversion step moved it by `0.000`. That leaves the model showing `63.2%` win probability and `64.4%` EV at `2.60`.
- What it means in plain English: the model still likes this side after smoothing recent form and pulling the player back toward his longer-run baseline, so this is not just a one-hot-game bet.
- Why it made the card: Model data projects 1.0 goals avg against a 0.5 line, creating a +0.5 stat gap for the over. The Markov state path is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price/EV state, and finishes with 95.0 QI. Model probability is 63.2% versus market 38.5%, producing 64.4% EV.
- Main risk: Goals are highest variance; price must compensate for scoring role volatility.

### Tom McCarthy Disposals Under 25.5 @ 1.89 (SportsBet)
- QI: 95.0
- Markov path: Strong -> Dominant -> Mispriced -> Elite
- Average bettor read: the adjusted model line is `22.304` against a market line of `25.5`. The raw season line was `22.000`, and the Kalman/reversion step moved it by `0.304`. That leaves the model showing `71.4%` win probability and `34.9%` EV at `1.89`.
- What it means in plain English: the model still likes this side after smoothing recent form and pulling the player back toward his longer-run baseline, so this is not just a one-hot-game bet.
- Why it made the card: Model data projects 22.304 disposals against a 25.5 line, creating a +3.2 stat gap for the under. The Markov state path is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price/EV state, and finishes with 95.0 QI. Model probability is 71.4% versus market 49.3%, producing 34.9% EV.
- Main risk: Disposal props are more stable, but role/rotation drift can still break projection.

### Conor Stone Disposals Over 17.5 @ 1.94 (SportsBet)
- QI: 93.5
- Markov path: Strong -> Dominant -> Mispriced -> Elite
- Average bettor read: the adjusted model line is `22.000` against a market line of `17.5`. The raw season line was `22.000`, and the Kalman/reversion step moved it by `0.000`. That leaves the model showing `77.0%` win probability and `49.4%` EV at `1.94`.
- What it means in plain English: the model still likes this side after smoothing recent form and pulling the player back toward his longer-run baseline, so this is not just a one-hot-game bet.
- Why it made the card: Model data projects 22.0 disposals against a 17.5 line, creating a +4.5 stat gap for the over. The Markov state path is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price/EV state, and finishes with 93.5 QI. Model probability is 77.0% versus market 48.1%, producing 49.4% EV.
- Main risk: Disposal props are more stable, but role/rotation drift can still break projection.

### Archie Roberts Disposals Over 29.5 @ 1.87 (PointsBet (AU))
- QI: 93.5
- Markov path: Strong -> Dominant -> Mispriced -> Elite
- Average bettor read: the adjusted model line is `33.667` against a market line of `29.5`. The raw season line was `32.455`, and the Kalman/reversion step moved it by `1.212`. That leaves the model showing `75.1%` win probability and `40.4%` EV at `1.87`.
- What it means in plain English: the model still likes this side after smoothing recent form and pulling the player back toward his longer-run baseline, so this is not just a one-hot-game bet.
- Why it made the card: Model data projects 33.667 disposals against a 29.5 line, creating a +4.2 stat gap for the over. The Markov state path is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price/EV state, and finishes with 93.5 QI. Model probability is 75.1% versus market 50.0%, producing 40.4% EV.
- Main risk: Disposal props are more stable, but role/rotation drift can still break projection.

### Kyle Langford Disposals Under 20.5 @ 1.87 (PointsBet (AU))
- QI: 93.5
- Markov path: Strong -> Dominant -> Mispriced -> Elite
- Average bettor read: the adjusted model line is `17.148` against a market line of `20.5`. The raw season line was `16.727`, and the Kalman/reversion step moved it by `0.421`. That leaves the model showing `72.1%` win probability and `34.9%` EV at `1.87`.
- What it means in plain English: the model still likes this side after smoothing recent form and pulling the player back toward his longer-run baseline, so this is not just a one-hot-game bet.
- Why it made the card: Model data projects 17.148 disposals against a 20.5 line, creating a +3.4 stat gap for the under. The Markov state path is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price/EV state, and finishes with 93.5 QI. Model probability is 72.1% versus market 50.0%, producing 34.9% EV.
- Main risk: Disposal props are more stable, but role/rotation drift can still break projection.

### Sullivan Robey Disposals Under 20.5 @ 1.87 (PointsBet (AU))
- QI: 93.5
- Markov path: Strong -> Dominant -> Mispriced -> Elite
- Average bettor read: the adjusted model line is `16.728` against a market line of `20.5`. The raw season line was `15.857`, and the Kalman/reversion step moved it by `0.871`. That leaves the model showing `72.7%` win probability and `36.0%` EV at `1.87`.
- What it means in plain English: the model still likes this side after smoothing recent form and pulling the player back toward his longer-run baseline, so this is not just a one-hot-game bet.
- Why it made the card: Model data projects 16.728 disposals against a 20.5 line, creating a +3.8 stat gap for the under. The Markov state path is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price/EV state, and finishes with 93.5 QI. Model probability is 72.7% versus market 50.0%, producing 36.0% EV.
- Main risk: Disposal props are more stable, but role/rotation drift can still break projection.

### Leek Aleer Tackles Over 3.5 @ 2.90 (PointsBet (AU))
- QI: 93.0
- Markov path: Strong -> Dominant -> Mispriced -> Elite
- Average bettor read: the adjusted model line is `4.606` against a market line of `3.5`. The raw season line was `4.333`, and the Kalman/reversion step moved it by `0.273`. That leaves the model showing `63.1%` win probability and `83.1%` EV at `2.90`.
- What it means in plain English: the model still likes this side after smoothing recent form and pulling the player back toward his longer-run baseline, so this is not just a one-hot-game bet.
- Why it made the card: Model data projects 4.606 tackles against a 3.5 line, creating a +1.1 stat gap for the over. The Markov state path is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price/EV state, and finishes with 93.0 QI. Model probability is 63.1% versus market 34.5%, producing 83.1% EV.
- Ladder context: Over 3.5 @ 2.9 EV 83.1%; Over 1.5 @ 1.25 EV 13.8%
- Main risk: Tackle props depend on game script and pressure exposure.

### Andy Moniz-Wakefield Goals Over 0.5 @ 2.45 (Betr)
- QI: 92.0
- Markov path: Strong -> Dominant -> Mispriced -> Elite
- Average bettor read: the adjusted model line is `1.000` against a market line of `0.5`. The raw season line was `1.000`, and the Kalman/reversion step moved it by `0.000`. That leaves the model showing `63.2%` win probability and `54.9%` EV at `2.45`.
- What it means in plain English: the model still likes this side after smoothing recent form and pulling the player back toward his longer-run baseline, so this is not just a one-hot-game bet.
- Why it made the card: Model data projects 1.0 goals avg against a 0.5 line, creating a +0.5 stat gap for the over. The Markov state path is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price/EV state, and finishes with 92.0 QI. Model probability is 63.2% versus market 40.8%, producing 54.9% EV.
- Main risk: Goals are highest variance; price must compensate for scoring role volatility.

### Will Setterfield Goals Over 0.5 @ 3.15 (Bet Right)
- QI: 92.0
- Markov path: Strong -> Dominant -> Mispriced -> Elite
- Average bettor read: the adjusted model line is `1.000` against a market line of `0.5`. The raw season line was `1.000`, and the Kalman/reversion step moved it by `0.000`. That leaves the model showing `63.2%` win probability and `99.1%` EV at `3.15`.
- What it means in plain English: the model still likes this side after smoothing recent form and pulling the player back toward his longer-run baseline, so this is not just a one-hot-game bet.
- Why it made the card: Model data projects 1.0 goals avg against a 0.5 line, creating a +0.5 stat gap for the over. The Markov state path is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price/EV state, and finishes with 92.0 QI. Model probability is 63.2% versus market 31.7%, producing 99.1% EV.
- Main risk: Goals are highest variance; price must compensate for scoring role volatility.
