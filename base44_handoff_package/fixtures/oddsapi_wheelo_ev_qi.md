# Odds API + Model Data EV/QI

Source markets: The Odds API + current Model data player pack.
Marks: Odds API returned INVALID_MARKET for player_marks/player_marks_over.

## Availability
- Carlton Blues v Geelong Cats: 10 bookmakers returned for player_afl_fantasy_points_over, player_disposals, player_goals_scored_over, player_tackles_over.
- Sydney Swans v Richmond Tigers: 10 bookmakers returned for player_afl_fantasy_points_over, player_disposals, player_goals_scored_over, player_tackles_over.
- Brisbane Lions v Fremantle Dockers: 10 bookmakers returned for player_afl_fantasy_points_over, player_disposals, player_goals_scored_over, player_tackles_over.
- Western Bulldogs v Collingwood Magpies: 10 bookmakers returned for player_afl_fantasy_points_over, player_disposals, player_goals_scored_over, player_tackles_over.
- Melbourne Demons v Greater Western Sydney Giants: 10 bookmakers returned for player_afl_fantasy_points_over, player_disposals, player_goals_scored_over, player_tackles_over.
- West Coast Eagles v Essendon Bombers: 10 bookmakers returned for player_afl_fantasy_points_over, player_disposals, player_goals_scored_over, player_tackles_over.

## Walters Portfolio Card
Rules: max 10 bets, max 3 goal props, max 1 per player; goals are stake-discounted.

| Signal | Stake | Player | Market | Side | Line | Price | Book | Proj | Prob | EV | QI | AltScore |
|---|---:|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
| A_BET | 0.50u | Liam Fawcett | Goals | Over | 1.5 | 4.00 | TAB | 2.1 | 62.8% | 151.1% | 95.0 | 0.8302 |
| A_BET | 0.50u | Hayden McLean | Goals | Over | 2.5 | 4.50 | TAB | 3.0 | 57.7% | 159.6% | 95.0 | 0.8227 |
| A_BET | 0.50u | Noah Roberts-Thomson | Goals | Over | 0.5 | 2.35 | SportsBet | 1.5 | 77.7% | 82.6% | 95.0 | 0.5322 |
| A_BET | 1.00u | Dion Prestia | Disposals | Under | 22.5 | 1.87 | PointsBet (AU) | 17.4 | 78.7% | 47.2% | 93.5 | 0.3761 |
| A_BET | 1.00u | Matthew Johnson | Disposals | Under | 18.5 | 1.95 | PointsBet (AU) | 15.4 | 70.5% | 37.4% | 95.0 | 0.2786 |
| A_BET | 1.00u | Sullivan Robey | Disposals | Under | 20.5 | 1.87 | PointsBet (AU) | 16.7 | 72.7% | 36.0% | 93.5 | 0.2701 |
| A_BET | 1.00u | Tom McCarthy | Disposals | Under | 25.5 | 1.89 | SportsBet | 22.3 | 71.4% | 34.9% | 95.0 | 0.2655 |
| A_BET | 1.00u | Kyle Langford | Disposals | Under | 20.5 | 1.87 | PointsBet (AU) | 17.1 | 72.1% | 34.9% | 93.5 | 0.2604 |
| A_BET | 1.00u | George Hewett | Disposals | Under | 23.5 | 1.87 | PointsBet (AU) | 20.3 | 71.2% | 33.1% | 93.5 | 0.2446 |
| A_BET | 1.00u | Toby Greene | Disposals | Over | 17.5 | 1.90 | PointsBet (AU) | 20.7 | 70.2% | 33.4% | 93.5 | 0.2440 |

## Suppressed A/B Edges
These remain model-positive but were removed by Walters portfolio discipline.
- Hugh McCluggage Disposals Under 22.5 @ 1.87 (PointsBet (AU)): SUPPRESSED_PORTFOLIO_CAP, EV 28.1%, QI 95.0
- Paddy Cross Goals Over 0.5 @ 2.15 (Betr): SUPPRESSED_GOAL_CAP, EV 35.9%, QI 90.7
- Archie Roberts Disposals Over 30.5 @ 1.80 (PointsBet (AU)): SUPPRESSED_PORTFOLIO_CAP, EV 25.4%, QI 93.1
- Shaun Mannagh Goals Over 1.5 @ 2.15 (Ladbrokes): SUPPRESSED_GOAL_CAP, EV 34.2%, QI 92.9
- Brent Daniels Goals Over 0.5 @ 1.60 (Betr): SUPPRESSED_GOAL_CAP, EV 26.5%, QI 93.6
- Lachie Neale Disposals Over 28.5 @ 1.89 (SportsBet): SUPPRESSED_PORTFOLIO_CAP, EV 25.4%, QI 86.0
- Tim Taranto Disposals Under 25.5 @ 1.87 (PointsBet (AU)): SUPPRESSED_PORTFOLIO_CAP, EV 25.2%, QI 84.5
- Sam Banks Disposals Under 18.5 @ 1.87 (PointsBet (AU)): SUPPRESSED_PORTFOLIO_CAP, EV 24.9%, QI 84.3
- Chad Warner Disposals Under 22.5 @ 1.87 (PointsBet (AU)): SUPPRESSED_PORTFOLIO_CAP, EV 24.4%, QI 84.0
- Zac Bailey Disposals Over 17.5 @ 1.92 (SportsBet): SUPPRESSED_PORTFOLIO_CAP, EV 23.9%, QI 85.0
- Jake Stringer Goals Over 1.5 @ 1.95 (TAB): SUPPRESSED_GOAL_CAP, EV 27.4%, QI 91.0
- Xavier Duursma Disposals Under 17.5 @ 1.87 (PointsBet (AU)): SUPPRESSED_PORTFOLIO_CAP, EV 23.7%, QI 83.6
- Will Setterfield Disposals Under 18.5 @ 1.87 (PointsBet (AU)): SUPPRESSED_PORTFOLIO_CAP, EV 23.3%, QI 83.4
- Liam Duggan Disposals Under 21.5 @ 1.87 (PointsBet (AU)): SUPPRESSED_PORTFOLIO_CAP, EV 22.1%, QI 82.8
- Corey Wagner Disposals Over 16.5 @ 1.83 (SportsBet): SUPPRESSED_PORTFOLIO_CAP, EV 20.9%, QI 82.6
- Elliot Yeo Tackles Over 4.5 @ 1.68 (SportsBet): SUPPRESSED_PORTFOLIO_CAP, EV 19.2%, QI 87.9
- Murphy Reid Disposals Over 22.5 @ 1.87 (PointsBet (AU)): SUPPRESSED_PORTFOLIO_CAP, EV 19.7%, QI 83.0
- Nathan O'Driscoll Disposals Over 17.5 @ 1.87 (PointsBet (AU)): SUPPRESSED_PORTFOLIO_CAP, EV 19.7%, QI 83.0
- Max Gruzewski Goals Over 1.5 @ 2.40 (Betr): SUPPRESSED_GOAL_CAP, EV 26.5%, QI 88.1
- Jack Ison Goals Over 0.5 @ 1.93 (Bet Right): SUPPRESSED_GOAL_CAP, EV 22.0%, QI 88.4

## Ladder Notes
- Liam Fawcett Goals Over: Over 1.5 @ 4.0 EV 151.1%; Over 0.5 @ 1.47 EV 29.5%
- Hayden McLean Goals Over: Over 2.5 @ 4.5 EV 159.6%; Over 1.5 @ 2.15 EV 72.2%; Over 0.5 @ 1.19 EV 13.1%
- Noah Roberts-Thomson Goals Over: Over 0.5 @ 2.35 EV 82.6%; Over 1.5 @ 10.0 EV 342.2%
- George Hewett Disposals Under: Under 23.5 @ 1.87 EV 33.1%; Under 22.5 @ 1.9 EV 23.6%

## Signal Counts
- A_BET: 42
- B_BET: 70
- INFO_ONLY: 3117
- LEAN: 26
- NO_MATCH: 155
- PASS: 2982

QI note: `live_qi` is a current-line confidence score derived from Model data support, model edge, market reliability, and book availability. It is not the historical BetMate QI field.
