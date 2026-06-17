# Odds API + Model Data EV/QI

Source markets: The Odds API + current Model data player pack.
Marks: Odds API returned INVALID_MARKET for player_marks/player_marks_over.

## Availability
- Fremantle Dockers v Geelong Cats: 10 bookmakers returned for player_afl_fantasy_points_over, player_disposals, player_goals_scored_over, player_tackles_over.
- Gold Coast Suns v Hawthorn Hawks: 10 bookmakers returned for player_afl_fantasy_points_over, player_disposals, player_goals_scored_over, player_tackles_over.
- Adelaide Crows v Melbourne Demons: 10 bookmakers returned for player_afl_fantasy_points_over, player_disposals, player_goals_scored_over, player_tackles_over.
- Greater Western Sydney Giants v Carlton Blues: 10 bookmakers returned for player_afl_fantasy_points_over, player_disposals, player_goals_scored_over, player_tackles_over.
- Collingwood Magpies v Port Adelaide Power: 10 bookmakers returned for player_afl_fantasy_points_over, player_disposals, player_goals_scored_over, player_tackles_over.
- Richmond Tigers v North Melbourne Kangaroos: 10 bookmakers returned for player_afl_fantasy_points_over, player_disposals, player_goals_scored_over, player_tackles_over.
- St Kilda Saints v Western Bulldogs: 10 bookmakers returned for player_afl_fantasy_points_over, player_disposals, player_goals_scored_over, player_tackles_over.

## Walters Portfolio Card
Rules: max 10 bets, max 3 goal props, max 1 per player; Thorp fractional Kelly sizes every selected edge and goals are stake-discounted.
Calibration: posterior probability blends model, market, and settled-history segments; max per game 3.

| Signal | Stake | Bankroll | Full Kelly | Player | Market | Side | Line | Price | Book | Proj | Post Prob | Post EV | QI | AltScore |
|---|---:|---:|---:|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|

## Suppressed A/B Edges
These remain model-positive but were removed by Walters portfolio discipline.
- Angus Hastie Tackles Over 3.5 @ 2.10 (PointsBet (AU)): SUPPRESSED_PREMIUM_RULE, post EV 21.0%, QI 93.0
- Willem Drew Tackles Over 5.5 @ 2.15 (SportsBet): NOT_SELECTED, post EV 20.2%, QI 81.3
- Shai Bolton Disposals Over 21.5 @ 1.87 (PointsBet (AU)): NOT_SELECTED, post EV 15.5%, QI 85.4
- Nathan O'Driscoll Disposals Over 18.5 @ 1.87 (PointsBet (AU)): NOT_SELECTED, post EV 15.1%, QI 83.7
- Oliver Dempsey Disposals Over 16.5 @ 1.87 (PointsBet (AU)): NOT_SELECTED, post EV 14.5%, QI 84.6
- Karl Worner Disposals Over 16.5 @ 1.87 (PointsBet (AU)): NOT_SELECTED, post EV 13.9%, QI 82.6
- Toby Greene Disposals Over 17.5 @ 1.87 (PointsBet (AU)): NOT_SELECTED, post EV 13.6%, QI 82.3
- Max Holmes Disposals Over 27.5 @ 1.87 (PointsBet (AU)): NOT_SELECTED, post EV 12.4%, QI 82.8
- Lawson Humphries Disposals Over 19.5 @ 1.87 (PointsBet (AU)): NOT_SELECTED, post EV 11.9%, QI 80.8
- Murphy Reid Disposals Over 22.5 @ 1.87 (PointsBet (AU)): NOT_SELECTED, post EV 10.7%, QI 81.2
- Harvey Harrison Tackles Over 4.5 @ 1.89 (SportsBet): SUPPRESSED_PREMIUM_RULE, post EV 11.3%, QI 84.8
- Cooper Harvey Tackles Over 2.5 @ 1.72 (SportsBet): SUPPRESSED_PREMIUM_RULE, post EV 10.1%, QI 87.0
- Scott Pendlebury Disposals Over 23.5 @ 1.87 (PointsBet (AU)): NOT_SELECTED, post EV 9.7%, QI 78.8
- Patrick Cripps Disposals Over 25.5 @ 1.87 (PointsBet (AU)): NOT_SELECTED, post EV 9.7%, QI 78.7
- Jayden Short Disposals Over 22.5 @ 1.87 (PointsBet (AU)): NOT_SELECTED, post EV 8.7%, QI 79.3
- Jack Ross Disposals Over 21.5 @ 1.87 (PointsBet (AU)): NOT_SELECTED, post EV 8.6%, QI 77.8
- Caleb Serong Disposals Over 23.5 @ 1.87 (SportsBet): NOT_SELECTED, post EV 8.2%, QI 79.1
- Colby McKercher Disposals Under 23.5 @ 2.00 (PointsBet (AU)): SUPPRESSED_PREMIUM_RULE, post EV 7.1%, QI 93.5
- Joe Richards Disposals Under 20.5 @ 1.87 (PointsBet (AU)): NOT_SELECTED, post EV 7.0%, QI 85.5
- Bodhi Uwland Disposals Over 22.5 @ 1.87 (PointsBet (AU)): NOT_SELECTED, post EV 7.5%, QI 76.8

## Ladder Notes

## Signal Counts
- A_BET: 5
- B_BET: 43
- INFO_ONLY: 3464
- LEAN: 13
- NO_MATCH: 57
- PASS: 2760

QI note: `live_qi` is a current-line confidence score derived from Model data support, model edge, market reliability, and book availability. It is not the historical BetMate QI field.
