# Odds API + Model Data EV/QI

Source markets: The Odds API + current Model data player pack.
Marks: Odds API returned INVALID_MARKET for player_marks/player_marks_over.

## Availability
- Adelaide Crows v Geelong Cats: 6 bookmakers returned for player_afl_fantasy_points_over, player_disposals, player_goals_scored_over, player_tackles_over.
- Hawthorn Hawks v Western Bulldogs: 6 bookmakers returned for player_afl_fantasy_points_over, player_disposals, player_goals_scored_over, player_tackles_over.
- North Melbourne Kangaroos v Fremantle Dockers: 4 bookmakers returned for player_afl_fantasy_points_over, player_disposals, player_goals_scored_over.
- Gold Coast Suns v Brisbane Lions: 4 bookmakers returned for player_afl_fantasy_points_over, player_disposals, player_goals_scored_over.
- West Coast Eagles v Port Adelaide Power: 1 bookmakers returned for player_goals_scored_over.
- Sydney Swans v St Kilda Saints: 5 bookmakers returned for player_afl_fantasy_points_over, player_disposals, player_goals_scored_over.
- Essendon Bombers v Carlton Blues: 1 bookmakers returned for player_goals_scored_over.
- Collingwood Magpies v Melbourne Demons: 0 bookmakers returned for requested player prop markets.

## Walters Portfolio Card
Rules: max 10 bets, max 3 goal props, max 1 per player; Thorp fractional Kelly sizes every selected edge and goals are stake-discounted.

| Signal | Stake | Bankroll | Full Kelly | Player | Market | Side | Line | Price | Book | Proj | Prob | EV | QI | AltScore |
|---|---:|---:|---:|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
| A_BET | 0.75u | 0.75% | 57.22% | Hayden McLean | Goals | Over | 2.5 | 4.00 | Ladbrokes | 3.5 | 67.9% | 171.7% | 95.0 | 1.0004 |
| A_BET | 0.75u | 0.75% | 39.68% | Shaun Mannagh | Goals | Over | 1.5 | 2.95 | SportsBet | 2.0 | 60.1% | 77.4% | 95.0 | 0.4115 |
| A_BET | 1.00u | 2.00% | 48.09% | Jake Soligo | Disposals | Under | 20.5 | 1.70 | PointsBet (AU) | 15.8 | 78.6% | 33.7% | 93.5 | 0.2678 |
| A_BET | 1.00u | 2.00% | 39.37% | Isaac Heeney | Disposals | Over | 24.5 | 1.87 | PointsBet (AU) | 28.1 | 71.8% | 34.2% | 95.0 | 0.2586 |
| A_BET | 0.75u | 0.75% | 40.24% | Jordan Dawson | Goals | Over | 0.5 | 1.99 | Bet Right | 1.2 | 70.3% | 39.8% | 93.5 | 0.2344 |
| A_BET | 1.00u | 1.25% | 24.37% | Ed Richards | Tackles | Over | 3.5 | 1.94 | SportsBet | 4.5 | 63.4% | 22.9% | 85.3 | 0.1276 |

## Suppressed A/B Edges
These remain model-positive but were removed by Walters portfolio discipline.
- Ned Moyle Goals Over 0.5 @ 2.10 (SportsBet): SUPPRESSED_GOAL_CAP, EV 32.7%, QI 89.6
- Liam Ryan Goals Over 0.5 @ 1.56 (PointsBet (AU)): SUPPRESSED_GOAL_CAP, EV 26.3%, QI 92.3
- Bailey J. Williams Goals Over 0.5 @ 2.20 (SportsBet): SUPPRESSED_GOAL_CAP, EV 30.6%, QI 86.4
- Ed Richards Goals Over 0.5 @ 1.92 (Bet Right): SUPPRESSED_GOAL_CAP, EV 26.5%, QI 89.3
- Jed Walter Goals Over 1.5 @ 2.12 (SportsBet): SUPPRESSED_GOAL_CAP, EV 25.9%, QI 89.2
- Jack Darling Goals Over 0.5 @ 1.48 (SportsBet): SUPPRESSED_GOAL_CAP, EV 18.8%, QI 86.7
- Will McLachlan Goals Over 0.5 @ 1.92 (SportsBet): SUPPRESSED_GOAL_CAP, EV 21.4%, QI 85.1
- Oliver Henry Goals Over 1.5 @ 2.10 (SportsBet): SUPPRESSED_GOAL_CAP, EV 21.3%, QI 87.2
- Blake Hardwick Disposals Under 18.5 @ 1.87 (PointsBet (AU)): NOT_SELECTED, EV 17.0%, QI 80.1
- Matt Rowell Disposals Under 26.5 @ 1.95 (SportsBet): NOT_SELECTED, EV 17.1%, QI 79.8
- Jordan Dawson Disposals Over 24.5 @ 1.87 (PointsBet (AU)): NOT_SELECTED, EV 14.9%, QI 82.5
- Ryley Sanders Disposals Over 25.5 @ 1.87 (PointsBet (AU)): NOT_SELECTED, EV 15.1%, QI 80.5
- James Sicily Disposals Under 23.5 @ 1.90 (SportsBet): NOT_SELECTED, EV 14.8%, QI 80.4
- Nasiah Wanganeen-Milera Disposals Over 26.5 @ 1.88 (SportsBet): NOT_SELECTED, EV 13.5%, QI 79.8
- Bradley Hill Disposals Over 20.5 @ 1.87 (PointsBet (AU)): NOT_SELECTED, EV 13.0%, QI 78.0
- Luke Parker Disposals Over 23.5 @ 1.85 (SportsBet): NOT_SELECTED, EV 12.8%, QI 78.1
- Caleb Daniel Disposals Over 22.5 @ 1.85 (SportsBet): NOT_SELECTED, EV 12.2%, QI 77.8
- Tanner Bruhn Disposals Under 22.5 @ 1.87 (PointsBet (AU)): NOT_SELECTED, EV 11.9%, QI 78.9
- Josh Ward Disposals Over 20.5 @ 1.87 (PointsBet (AU)): NOT_SELECTED, EV 11.7%, QI 77.2
- Sam Berry Disposals Over 21.5 @ 1.87 (PointsBet (AU)): NOT_SELECTED, EV 10.8%, QI 76.7

## Ladder Notes
- Hayden McLean Goals Over: Over 2.5 @ 4.0 EV 171.7%; Over 1.5 @ 1.96 EV 69.4%; Over 0.5 @ 1.18 EV 14.4%; Over 3.5 @ 10.0 EV 363.4%
- Shaun Mannagh Goals Over: Over 1.5 @ 2.95 EV 77.4%; Over 0.5 @ 1.44 EV 25.0%
- Ed Richards Tackles Over: Over 3.5 @ 1.94 EV 22.9%; Over 2.5 @ 1.35 EV 7.4%; Over 4.5 @ 3.15 EV 46.0%

## Signal Counts
- A_BET: 17
- B_BET: 24
- INFO_ONLY: 581
- LEAN: 29
- NO_MATCH: 46
- PASS: 1298

QI note: `live_qi` is a current-line confidence score derived from Model data support, model edge, market reliability, and book availability. It is not the historical BetMate QI field.
