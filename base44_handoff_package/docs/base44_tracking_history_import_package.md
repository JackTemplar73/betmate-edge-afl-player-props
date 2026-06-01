# Base44 Tracking History Import Package

Use this package to restore and preserve existing AFL tracking/performance inside Base44.

## Goal

Base44 must import the existing historical ledger and use it as the source of truth for:
- `Tracking`
- `History`
- settled performance metrics
- Saints/Hawks results already captured in Codex

This is required so we do **not** lose the tracked results from `St Kilda Saints v Hawthorn Hawks`.

---

## Problem

The app is not showing current tracked bets and performance because it is relying on current live `Prop` rows instead of the historical ledger.

That is the wrong source.

Use:
- `Prop` for current round live state only
- `BetHistory` for historical tracking, settlement, CLV, and performance

---

## Files To Import

Primary import file:
- `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/base44_handoff_package/exports/base44_bet_history_import.csv`

JSON alternative:
- `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/base44_handoff_package/exports/base44_bet_history_import.json`

Verification summary:
- `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/base44_handoff_package/exports/base44_tracking_summary.json`

Source ledger from Codex:
- `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/aflplayerprops_bet_history.csv`

Round mapping source:
- `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/afl_round_mapping.csv`

---

## Entity To Create

Create a dedicated entity:

`BetHistory`

Fields:
- `betId`
- `status`
- `createdAtUtc`
- `updatedAtUtc`
- `roundNumber`
- `game`
- `commenceTime`
- `player`
- `market`
- `side`
- `line`
- `book`
- `betPrice`
- `stakeUnits`
- `signal`
- `projection`
- `modelProbability`
- `marketProbability`
- `modelEdge`
- `evPerUnit`
- `qi`
- `altLineScore`
- `markovPath`
- `bookMarketReliability`
- `portfolioSelection`
- `openLine`
- `openPrice`
- `latestLine`
- `latestPrice`
- `closeLine`
- `closePrice`
- `clvPriceDecimal`
- `clvImpliedPoints`
- `lineClv`
- `clvStatus`
- `actual`
- `result`
- `flatProfit`
- `stakeProfit`

---

## Import Rules

- Use `betId` as the stable unique key.
- Upsert rows by `betId`.
- Preserve all existing values exactly from the CSV.
- Do not drop settled rows.
- Do not overwrite `BetHistory` from live `Prop` refreshes.
- Never clear `BetHistory` during a current-round refresh.
- `Prop` is for current live/current-round rows only.
- `BetHistory` is the source of truth for `Tracking` and `History`.

---

## Frontend Rules

### Tracking tab

- Read from `BetHistory`
- Show started/completed rows
- Calculate performance from `BetHistory`, not `Prop`

### History tab

- Read from all `BetHistory` rows
- First columns:
  - `Date`
  - `Round`
- Then render the rest of the tracking-style fields

### Performance math

Use settled `BetHistory` rows only:
- `Equal Bet Profit` = sum(`flatProfit`)
- `Actual Profit` = sum(`stakeProfit`)
- `Actual ROI` = sum(`stakeProfit`) / sum(`stakeUnits`) * 100

---

## Verification Targets

After import, Base44 must show this exact Saints/Hawks record.

### Game

`St Kilda Saints v Hawthorn Hawks`

### Expected totals

- `rowCount`: `34`
- `settledCount`: `34`
- `WIN`: `21`
- `LOSS`: `10`
- `PUSH`: `3`
- `Equal Bet Profit`: `6.63`
- `Actual Profit`: `3.266`
- `Total Staked`: `7.2`
- `Actual ROI`: `45.4%`

### Overall imported totals

- `rowCount`: `178`
- `settledCount`: `44`
- `WIN`: `27`
- `LOSS`: `14`
- `PUSH`: `3`
- `Equal Bet Profit`: `7.45`
- `Actual Profit`: `4.131`
- `Total Staked`: `12.25`
- `Actual ROI`: `33.7%`

These targets come from:
- `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/base44_handoff_package/exports/base44_tracking_summary.json`

---

## Backend Functions To Add

### 1. `importBetHistory`

Purpose:
- one-time import of the existing ledger into Base44

Behavior:
1. load `base44_bet_history_import.csv` or `.json`
2. upsert into `BetHistory` by `betId`
3. preserve every field exactly
4. return import counts and verification totals

### 2. `syncBetHistory`

Purpose:
- ongoing sync after refreshes and settlements

Behavior:
1. read the latest Codex-exported history rows
2. upsert by `betId`
3. update rows when:
   - `status` changes
   - `actual` changes
   - `result` changes
   - `clv` fields change
   - `flatProfit` changes
   - `stakeProfit` changes
4. do not delete older history rows

---

## Backend Pseudocode

```ts
export async function importBetHistory(rows: BetHistoryImportRow[]) {
  let created = 0;
  let updated = 0;

  for (const row of rows) {
    const existing = await entities.BetHistory.filter({ betId: row.betId });

    if (existing.length > 0) {
      await entities.BetHistory.update(existing[0].id, row);
      updated += 1;
    } else {
      await entities.BetHistory.create(row);
      created += 1;
    }
  }

  return {
    ok: true,
    imported: rows.length,
    created,
    updated,
  };
}

export async function syncBetHistory(rows: BetHistoryImportRow[]) {
  let created = 0;
  let updated = 0;

  for (const row of rows) {
    const existing = await entities.BetHistory.filter({ betId: row.betId });

    if (existing.length === 0) {
      await entities.BetHistory.create(row);
      created += 1;
      continue;
    }

    const current = existing[0];
    const changed =
      current.status !== row.status ||
      current.actual !== row.actual ||
      current.result !== row.result ||
      current.clvPriceDecimal !== row.clvPriceDecimal ||
      current.clvImpliedPoints !== row.clvImpliedPoints ||
      current.lineClv !== row.lineClv ||
      current.clvStatus !== row.clvStatus ||
      current.flatProfit !== row.flatProfit ||
      current.stakeProfit !== row.stakeProfit ||
      current.updatedAtUtc !== row.updatedAtUtc;

    if (changed) {
      await entities.BetHistory.update(current.id, row);
      updated += 1;
    }
  }

  return {
    ok: true,
    created,
    updated,
  };
}
```

---

## Required UI Query Rule

Do **not** build Tracking or History from the current `Prop` table.

Use:
- `Prop` for round-summary and match live views
- `BetHistory` for tracking/history/performance views

If this rule is broken, Saints/Hawks performance can disappear from the app even though it still exists in the ledger.

---

## Definition Of Done

The work is not complete until:
- Saints/Hawks tracking rows appear in `Tracking`
- Saints/Hawks rows appear in `History`
- performance totals match the verification targets above
- tracking/history survives future refreshes
- `BetHistory` remains intact when `Prop` is replaced on refresh

---

## Short Build Instruction

If you want the shortest possible instruction to Base44:

> Import `base44_bet_history_import.csv` into a new `BetHistory` entity keyed by `betId`. Drive `Tracking` and `History` from `BetHistory`, not `Prop`. Verify that `St Kilda Saints v Hawthorn Hawks` shows 34 settled rows, 21-10-3, +6.63 equal-bet profit, +3.266 actual profit, and 45.4% actual ROI.
