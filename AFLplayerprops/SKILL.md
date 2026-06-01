---
name: AFLplayerprops
description: >
  AFL player props betting agent for today's games. Use when asked to source AFL player prop bets from Model data and The Odds API, score disposals, tackles, goals, ranking/fantasy and available player prop markets, calculate EV/QI, select best alternate lines, produce Markov-chain-style commentary for average bettors, and export HTML/PDF bet cards.
metadata:
  short-description: AFL player props EV/QI and Markov bet cards
---

# AFLplayerprops

Use this agent for AFL player-prop betting analysis, especially requests like:

- "today's AFL player props"
- "use Model data and Odds API"
- "show EV and QI"
- "include alternate lines"
- "show Markov commentary"
- "produce HTML/PDF"

## Core Workflow

1. **Source Model data**
   - Fetch current player/team stats and match previews from the configured model-data source.
   - Use Model data as the primary projection/team-list source.
   - External-facing outputs must call this source **Model data**. Never mention the underlying vendor/source name in chat, HTML, PDF, Markdown reports, summaries, or automated run notes.

2. **Fetch Odds API markets**
   - Use The Odds API sport key `aussierules_afl`.
   - Region: `au`.
   - Primary markets:
     - `player_disposals`
     - `player_tackles_over`
     - `player_goals_scored_over`
     - `player_afl_fantasy_points_over`
   - Try marks only if supported, but note that The Odds API may return `INVALID_MARKET`.
   - If a game returns zero bookmakers, state that clearly and do not invent bets.

3. **Score EV/QI**
   - Join Odds API outcomes to the Model data selected-player pack.
   - Calculate model probability from Model data projection versus line using market-specific variance.
   - Calculate market probability from no-vig where both sides are present, otherwise raw implied probability.
   - Calculate EV as `model_probability * price - 1`.
   - Calculate live QI from Model support, model edge, market type, and book availability.

4. **Select alternate lines**
   - Do not list every positive line blindly.
   - Select one best risk-adjusted line per player/market/side.
   - Use the alt-line idea:
     - EV says "is the price good?"
     - Alt Score says "which version of the bet should we take?"
   - Keep ladder notes for useful alternatives.
   - Apply Walters portfolio discipline:
     - Maximum 6-10 bets by default.
     - Maximum 2-3 goal props unless the user explicitly wants a wide card.
     - Maximum 1 bet per player unless explicitly laddering.
     - Goals are stake-discounted because they are high variance.
     - Tackles/disposals can receive normal sizing when projection, probability, and price align.

5. **Explain in bettor-friendly Markov language**
   - Translate the chain as:
     - Does Model data like it?
     - Does probability agree?
     - Is the price wrong?
     - Is confidence high?
   - Markov path format:
     - `Projection support -> Probability edge -> Price/EV state -> QI confidence`
   - Example:
     - `Strong -> Dominant -> Mispriced -> Elite`
     - Means the projection supports the bet, the model probability strongly beats the market, the book price is wrong, and QI is elite.

6. **Export**
   - Produce a concise chat summary.
   - Produce an HTML report when requested.
   - Produce a PDF report when requested.

7. **Settle and learn without overreacting**
   - After matches, settle against official `AFL.com.au` match stats first.
   - Use Wheelo/Model before-v-after snapshots only as a fallback when official AFL stats are unavailable.
   - Treat one slate as a small Bayesian update, not proof.
   - Do not ban a bookmaker or market from one result.
   - Update gently:
     - goal overs receive a small volatility penalty after noisy losses;
     - PointsBet goal clusters receive a small reliability haircut until more data accumulates;
     - winning tackle signals receive a tiny positive nudge only when backed by projection and price.
   - Preserve CLV tracking as a required next evidence layer when opening and closing prices are available.

8. **Maintain persistent history**
   - Always keep a durable ledger named `aflplayerprops_bet_history.csv` in the active working directory unless the user specifies another path.
   - At card creation, append portfolio bets with `aflplayerprops_history.py log-card`.
   - On each odds refresh, update latest prices with `aflplayerprops_history.py update-clv`.
   - Near bounce or after the market disappears, run `aflplayerprops_history.py update-clv --close`.
   - After settlement, run `aflplayerprops_history.py settle`.
   - Summarise long-run record with `aflplayerprops_history.py summary`.
   - Never overwrite history manually. Append/update by `bet_id`.

## Recommended Script Sequence

The bundled scripts in `scripts/` are templates. Copy them into the active working directory or adapt the local copies already present.

Typical run order:

```bash
./fetch_wheelo_snapshots.sh
python3 extract_wheelo_today_pack.py
curl -L -o oddsapi_events.json "https://api.the-odds-api.com/v4/sports/aussierules_afl/events?apiKey=KEY"
curl -L -o oddsapi_GAME_props.json "https://api.the-odds-api.com/v4/sports/aussierules_afl/events/EVENT_ID/odds?apiKey=KEY&regions=au&markets=player_disposals,player_tackles_over,player_goals_scored_over,player_afl_fantasy_points_over&oddsFormat=decimal"
python3 score_oddsapi_wheelo_props.py
python3 markov_bet_justifications.py
python3 aflplayerprops_history.py log-card
# Repeat after refreshed Odds API snapshots:
python3 aflplayerprops_history.py update-clv
# Near bounce / final snapshot:
python3 aflplayerprops_history.py update-clv --close
python3 build_player_prop_summary_html.py
python3 build_player_prop_summary_pdf.py
python3 settle_player_props_from_wheelo.py --game "St Kilda v Hawthorn" --afl-match-url "https://www.afl.com.au/afl/matches/8139"  # after results are available
python3 aflplayerprops_history.py settle
python3 aflplayerprops_history.py summary
```

Settlement notes:

- `settle_player_props_from_wheelo.py` now defaults to official `AFL.com.au` player stats.
- Preferred inputs are `--afl-match-url`, `--afl-match-id`, or a local `afl_match_mapping.csv`.
- `afl_match_mapping.csv` should store: `game, commence_time, afl_match_id, afl_match_url, afl_provider_match_id`.
- The script reads the ledger first so game-targeted settlement uses the exact logged bets.
- Missing official player-stat rows are treated as `DNP` and settled as `PUSH`.
- Use `--source wheelo` only when official AFL stats are unavailable.

Use the bundled Python runtime when ReportLab/pypdf are needed:

```bash
/Users/merlin/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 build_player_prop_summary_pdf.py
```

## Grading Definitions

**A_BET**

- Approved market: disposals, tackles, or goals.
- Strong Model data support.
- Clear positive model edge.
- High QI.
- Markov path usually finishes `High` or `Elite`.
- Still size by volatility: an A goal prop may be a half-unit or quarter-unit, not a full-unit bet.

**B_BET**

- Approved market.
- Lean or strong Model data support.
- Positive EV.
- One softer state, such as smaller projection cushion, thinner price, lower QI, or higher volatility.

**LEAN**

- Interesting but not a bet by default.
- Needs price improvement, role confirmation, or another source of support.

**INFO_ONLY**

- Use for fantasy/ranking markets until separately backtest-approved.

## Output Discipline

- Never present unavailable markets as bets.
- Never mention the underlying model-data vendor/source name in any external-facing output; use "Model data" or "model projection" instead.
- Never bet a game that returned zero bookmakers.
- Clearly separate "model candidates" from "bettable lines".
- Show best AU bookie and price.
- Explain goal-prop variance plainly.
- Warn that prices can move and late team/role news can invalidate an edge.
- Default to the Walters portfolio card, not the full candidate list.
- Show suppressed A/B edges separately so the user sees what was removed by discipline.
- Track and report stake units, not only win/loss.
- Maintain `aflplayerprops_bet_history.csv` as the source of truth for all historical bets, CLV, settlement, and stake-adjusted profit.
