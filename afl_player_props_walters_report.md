# Walters Style AFL Player Props Report: Round 12 Current Portfolio

Generated: 2026-06-10 21:02

This card uses the adjusted model line from a simple Kalman-style recent-form update plus mean reversion back toward the season baseline before EV/QI scoring.

## Summary Card

| QI | Signal | Player | Market | Side | Model Line | Market Line | Price | Bookie | EV | Stake |
|---:|---|---|---|---|---:|---:|---:|---|---:|---:|
| 95.0 | A_BET | Ned Moyle | Goals | Over | 0.800 | 0.5 | 4.00 | PointsBet (AU) | 119.2% | 0.75u |
| 95.0 | A_BET | Sam Durham | Disposals | Under | 19.498 | 23.5 | 1.89 | SportsBet | 42.6% | 1.00u |
| 95.0 | A_BET | Hayden McLean | Goals | Over | 3.000 | 2.5 | 6.25 | SportsBet | 260.5% | 0.75u |
| 95.0 | A_BET | Max Gruzewski | Goals | Over | 2.077 | 1.5 | 2.70 | TAB | 65.9% | 0.75u |
| 93.5 | A_BET | Archie Roberts | Disposals | Over | 32.356 | 26.5 | 1.85 | SportsBet | 55.6% | 1.00u |
| 93.5 | A_BET | Daniel Curtin | Disposals | Under | 13.000 | 17.5 | 1.90 | PointsBet (AU) | 48.2% | 1.00u |
| 91.5 | A_BET | Luker Kentfield | Tackles | Over | 4.000 | 2.5 | 2.08 | SportsBet | 49.0% | 1.00u |
| 91.5 | A_BET | Tom Cochrane | Tackles | Over | 6.000 | 4.5 | 2.45 | SportsBet | 75.2% | 1.00u |
| 91.5 | A_BET | Angus Hastie | Tackles | Over | 8.000 | 6.5 | 7.25 | SportsBet | 397.8% | 1.00u |

## Detailed Markov Analysis

Plain-English frame: does the adjusted model support the bet, does the probability still beat the market after smoothing, is the price good enough, and is the confidence high enough to survive Walters-style filtering?

### Ned Moyle Goals Over 0.5 @ 4.00 (PointsBet (AU))
- QI: 95.0
- Markov path: Strong -> Dominant -> Mispriced -> Elite
- Average bettor read: the adjusted model line is `0.800` against a market line of `0.5`. The raw season line was `0.800`, and the Kalman/reversion step moved it by `0.000`. That leaves the model showing `54.8%` win probability and `119.2%` EV at `4.00`.
- What it means in plain English: the model still likes this side after smoothing recent form and pulling the player back toward his longer-run baseline, so this is not just a one-hot-game bet.
- Why it made the card: Model data projects 0.8 goals avg against a 0.5 line, creating a +0.3 stat gap for the over. The bet profile is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price check, and finishes with 95.0 QI. Model probability is 54.8% versus market 25.0%, creating a 29.8% probability edge.
- Main risk: Goals are highest variance; price must compensate for scoring role volatility.

### Sam Durham Disposals Under 23.5 @ 1.89 (SportsBet)
- QI: 95.0
- Markov path: Strong -> Dominant -> Mispriced -> Elite
- Average bettor read: the adjusted model line is `19.498` against a market line of `23.5`. The raw season line was `19.333`, and the Kalman/reversion step moved it by `0.165`. That leaves the model showing `75.4%` win probability and `42.6%` EV at `1.89`.
- What it means in plain English: the model still likes this side after smoothing recent form and pulling the player back toward his longer-run baseline, so this is not just a one-hot-game bet.
- Why it made the card: Model data projects 19.498 disposals against a 23.5 line, creating a +4.0 stat gap for the under. The bet profile is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price check, and finishes with 95.0 QI. Model probability is 75.4% versus market 49.3%, creating a 26.1% probability edge.
- Main risk: Disposal props are more stable, but role/rotation drift can still break projection.

### Hayden McLean Goals Over 2.5 @ 6.25 (SportsBet)
- QI: 95.0
- Markov path: Strong -> Dominant -> Mispriced -> Elite
- Average bettor read: the adjusted model line is `3.000` against a market line of `2.5`. The raw season line was `3.000`, and the Kalman/reversion step moved it by `0.000`. That leaves the model showing `57.7%` win probability and `260.5%` EV at `6.25`.
- What it means in plain English: the model still likes this side after smoothing recent form and pulling the player back toward his longer-run baseline, so this is not just a one-hot-game bet.
- Why it made the card: Model data projects 3.0 goals avg against a 2.5 line, creating a +0.5 stat gap for the over. The bet profile is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price check, and finishes with 95.0 QI. Model probability is 57.7% versus market 16.0%, creating a 41.7% probability edge.
- Ladder context: Over 2.5 @ 6.25 EV 260.5%; Over 1.5 @ 2.55 EV 104.2%; Over 0.5 @ 1.32 EV 25.4%
- Main risk: Goals are highest variance; price must compensate for scoring role volatility.

### Max Gruzewski Goals Over 1.5 @ 2.70 (TAB)
- QI: 95.0
- Markov path: Strong -> Dominant -> Mispriced -> Elite
- Average bettor read: the adjusted model line is `2.077` against a market line of `1.5`. The raw season line was `1.750`, and the Kalman/reversion step moved it by `0.327`. That leaves the model showing `61.4%` win probability and `65.9%` EV at `2.70`.
- What it means in plain English: the model still likes this side after smoothing recent form and pulling the player back toward his longer-run baseline, so this is not just a one-hot-game bet.
- Why it made the card: Model data projects 2.077 goals avg against a 1.5 line, creating a +0.6 stat gap for the over. The bet profile is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price check, and finishes with 95.0 QI. Model probability is 61.4% versus market 37.0%, creating a 24.4% probability edge.
- Ladder context: Over 1.5 @ 2.7 EV 65.9%; Over 0.5 @ 1.32 EV 15.5%
- Main risk: Goals are highest variance; price must compensate for scoring role volatility.

### Archie Roberts Disposals Over 26.5 @ 1.85 (SportsBet)
- QI: 93.5
- Markov path: Strong -> Dominant -> Mispriced -> Elite
- Average bettor read: the adjusted model line is `32.356` against a market line of `26.5`. The raw season line was `31.538`, and the Kalman/reversion step moved it by `0.818`. That leaves the model showing `84.1%` win probability and `55.6%` EV at `1.85`.
- What it means in plain English: the model still likes this side after smoothing recent form and pulling the player back toward his longer-run baseline, so this is not just a one-hot-game bet.
- Why it made the card: Model data projects 32.356 disposals against a 26.5 line, creating a +5.9 stat gap for the over. The bet profile is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price check, and finishes with 93.5 QI. Model probability is 84.1% versus market 50.4%, creating a 33.7% probability edge.
- Ladder context: Over 26.5 @ 1.85 EV 55.6%; Over 27.5 @ 1.87 EV 48.9%
- Main risk: Disposal props are more stable, but role/rotation drift can still break projection.

### Daniel Curtin Disposals Under 17.5 @ 1.90 (PointsBet (AU))
- QI: 93.5
- Markov path: Strong -> Dominant -> Mispriced -> Elite
- Average bettor read: the adjusted model line is `13.000` against a market line of `17.5`. The raw season line was `13.000`, and the Kalman/reversion step moved it by `0.000`. That leaves the model showing `78.0%` win probability and `48.2%` EV at `1.90`.
- What it means in plain English: the model still likes this side after smoothing recent form and pulling the player back toward his longer-run baseline, so this is not just a one-hot-game bet.
- Why it made the card: Model data projects 13.0 disposals against a 17.5 line, creating a +4.5 stat gap for the under. The bet profile is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price check, and finishes with 93.5 QI. Model probability is 78.0% versus market 49.1%, creating a 28.9% probability edge.
- Main risk: Disposal props are more stable, but role/rotation drift can still break projection.

### Luker Kentfield Tackles Over 2.5 @ 2.08 (SportsBet)
- QI: 91.5
- Markov path: Strong -> Dominant -> Mispriced -> Elite
- Average bettor read: the adjusted model line is `4.000` against a market line of `2.5`. The raw season line was `4.000`, and the Kalman/reversion step moved it by `0.000`. That leaves the model showing `71.7%` win probability and `49.0%` EV at `2.08`.
- What it means in plain English: the model still likes this side after smoothing recent form and pulling the player back toward his longer-run baseline, so this is not just a one-hot-game bet.
- Why it made the card: Model data projects 4.0 tackles against a 2.5 line, creating a +1.5 stat gap for the over. The bet profile is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price check, and finishes with 91.5 QI. Model probability is 71.7% versus market 48.1%, creating a 23.6% probability edge.
- Ladder context: Over 2.5 @ 2.08 EV 49.0%; Over 1.5 @ 1.34 EV 16.7%; Over 3.5 @ 3.8 EV 104.2%
- Main risk: Tackle props depend on game script and pressure exposure.

### Tom Cochrane Tackles Over 4.5 @ 2.45 (SportsBet)
- QI: 91.5
- Markov path: Strong -> Dominant -> Mispriced -> Elite
- Average bettor read: the adjusted model line is `6.000` against a market line of `4.5`. The raw season line was `6.000`, and the Kalman/reversion step moved it by `0.000`. That leaves the model showing `71.5%` win probability and `75.2%` EV at `2.45`.
- What it means in plain English: the model still likes this side after smoothing recent form and pulling the player back toward his longer-run baseline, so this is not just a one-hot-game bet.
- Why it made the card: Model data projects 6.0 tackles against a 4.5 line, creating a +1.5 stat gap for the over. The bet profile is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price check, and finishes with 91.5 QI. Model probability is 71.5% versus market 40.8%, creating a 30.7% probability edge.
- Ladder context: Over 4.5 @ 2.45 EV 75.2%; Over 3.5 @ 1.74 EV 47.7%; Over 2.5 @ 1.24 EV 16.3%; Over 5.5 @ 4.3 EV 138.4%
- Main risk: Tackle props depend on game script and pressure exposure.

### Angus Hastie Tackles Over 6.5 @ 7.25 (SportsBet)
- QI: 91.5
- Markov path: Strong -> Dominant -> Mispriced -> Elite
- Average bettor read: the adjusted model line is `8.000` against a market line of `6.5`. The raw season line was `8.000`, and the Kalman/reversion step moved it by `0.000`. That leaves the model showing `68.7%` win probability and `397.8%` EV at `7.25`.
- What it means in plain English: the model still likes this side after smoothing recent form and pulling the player back toward his longer-run baseline, so this is not just a one-hot-game bet.
- Why it made the card: Model data projects 8.0 tackles against a 6.5 line, creating a +1.5 stat gap for the over. The bet profile is Strong -> Dominant -> Mispriced -> Elite, meaning the row moves from projection support into a positive probability state, then through the price check, and finishes with 91.5 QI. Model probability is 68.7% versus market 13.8%, creating a 54.9% probability edge.
- Ladder context: Over 6.5 @ 7.25 EV 397.8%; Over 5.5 @ 4.0 EV 223.5%; Over 4.5 @ 2.45 EV 120.6%; Over 3.5 @ 1.67 EV 59.9%
- Main risk: Tackle props depend on game script and pressure exposure.
