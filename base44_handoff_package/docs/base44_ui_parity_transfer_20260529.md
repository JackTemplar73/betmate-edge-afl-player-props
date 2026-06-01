# Base44 UI Parity Transfer

This document tells Base44 how to reproduce the **look and feel** of the current BetMate Edge Codex report, not just the data model.

Reference artifact:

- current local HTML:
  - `/Users/merlin/Documents/Codex/2026-05-24/consider-all-our-existing-afl-related/afl_player_props_stk_haw_walters_report.html`
- packaged artifact:
  - `artifacts/afl_player_props_stk_haw_walters_report.html`

The goal is simple:

- same scan speed
- same table-first bettor workflow
- same visual hierarchy
- same live-vs-history emphasis
- same restrained trading-desk tone

## Design Intent

The app should feel like:

- a sharp betting desk
- a clean white research surface
- compact and information-dense
- calm, not flashy
- designed for fast scanning, not storytelling

It should **not** feel like:

- a generic dashboard template
- a heavy dark-mode trading app
- a consumer sportsbook
- a marketing landing page
- a card carousel product UI

## Core Visual Rules

### Background

Use:

- a white base
- a very light cool gradient wash
- subtle top-right radial accent

Target feel:

- quiet
- premium
- lightly atmospheric

Do not use:

- flat grey app-shell backgrounds
- dark mode
- saturated multicolor gradients

### Typography

Use a clean humanist sans stack close to:

- `"Avenir Next", "IBM Plex Sans", "Segoe UI", sans-serif`

Typography should feel:

- slightly editorial
- sharper than default system UI
- easy to scan in dense tables

### Color system

Base colors:

- `ink`: very dark slate, close to `#111827`
- `muted`: medium slate, close to `#4b5563`
- `line`: light grey border, close to `#d1d5db`
- `panel`: light cool background, close to `#f8fafc`
- `bg`: white

Accent direction:

- teal/blue family
- no purple-heavy global theme
- purple reserved for top QI pill band only

## Layout

### Header

Header should:

- span full width
- sit on white with slight transparency feel
- have a thin bottom border
- feel like a calm terminal/report masthead

Header spacing:

- top padding around `28px`
- left/right padding around `34px`
- bottom padding around `18px`

Header structure:

1. page title on the left
2. refresh controls on the right
3. generated/meta text underneath

### Main content

Main content padding:

- around `22px 34px 40px`

Do not crowd the edges.

### Section rhythm

Use generous but controlled vertical spacing:

- `h2` top margin around `28px`
- standard section gap around `28px`
- QI subgroup spacing around `22px`

There must be clear extra space above:

- `Multi Props Only`
- results summary blocks
- charts

## Header UI

### Title

Top page title must be:

- `BetMate Edge: Player Props`

Style:

- around `28px`
- strong weight
- no subtitle overload

### Refresh button

Style the refresh button like the current report:

- dark filled button
- white text
- rounded corners around `10px`
- compact but substantial padding
- subtle shadow
- hover darkens slightly

Do not style it like:

- a bright CTA
- a pill chip
- a flat text button

### Refresh status

Show status under the button:

- small text
- muted by default
- red only for errors
- right-aligned

## Tabs

Tabs must feel like:

- bettor workspace navigation
- not browser tabs
- not segmented mobile controls

Style:

- rounded pills
- thin border
- white inactive tabs
- dark active tab
- compact padding
- bold text

Tab bar spacing:

- around `18px` below the header/meta area

Tab order:

1. Round Summary
2. match tabs in game start order
3. History
4. Tracking last

## Cards

### Summary stat cards

Cards should:

- sit in a responsive grid
- white background
- thin border
- rounded corners around `12px`
- subtle shadow
- compact internal padding

The feel should be:

- analytical
- lightweight
- not oversized KPI tiles

### Results and chart cards

Use the same white card language:

- white panel
- thin grey border
- `12px` radius
- soft shadow

This should visually tie:

- recap cards
- results summaries
- charts
- best/worst lists

## Tables

Tables are the main product.

They should be:

- compact
- dense
- easy to scan line-by-line
- not oversized

### Table styling

Use:

- white background
- thin row dividers
- dark bold header row
- restrained zebra or no zebra
- compact cell padding

Do not use:

- giant padded enterprise rows
- colorful cells
- heavy box outlines around every cell

### Table emphasis

The live props tables should dominate the page visually.

History and tracking tables should feel:

- equally readable
- but secondary in hierarchy to the live current-round card

## QI Treatment

QI must be a pill, not plain text.

### QI pill style

Use:

- rounded capsule
- compact height
- centered numeral
- whole-number display only
- bold weight

### QI color bands

Use exactly:

- `90-100`: purple
- `85-89`: teal
- `80-84`: blue
- `75-79`: amber
- `70-74`: orange

The pill should be the primary color expression in the tables.

Do not spread those colors broadly through the whole app.

## Section Structure

Each tab should follow the same visual pattern:

1. `High Value Props`
2. QI subgroup blocks inside that section
3. extra space
4. `Multi Props Only`
5. QI subgroup blocks inside that section

Tracking and History add:

- results summary above tables
- charts in History
- Result column in tracking/history tables

## QI Grouping Presentation

When grouped, use these visible subgroup headings:

- `90-100 QI`
- `85-89 QI`
- `80-84 QI`

These subgroup headings should:

- be smaller than `h2`
- slightly muted
- uppercase or near-uppercase feel acceptable
- clearly separate table blocks

## Tracking Tab Feel

Tracking should look like:

- a performance review layer
- not the primary betting card

It needs:

- recap cards first
- separate results summary tables for:
  - High Value Props
  - Multi Props Only
- settled tables under that

Result labels should be easy to spot:

- `WIN`
- `LOSS`
- `PUSH`
- `IN PLAY`

Tracking must remain crisp and factual.

No verbose commentary blocks.

## History Tab Feel

History should feel:

- archival
- quantitative
- still clean

It should include:

- weekly profit chart
- monthly profit chart
- full historical rows

Charts should be:

- simple SVG or native chart equivalents
- thin axis lines
- muted labels
- no cartoon colors
- profit-first, not decorative

## Language / Copy Tone

UI copy should stay:

- short
- betting-literate
- operational

Avoid:

- onboarding copy
- marketing slogans
- long helper paragraphs
- AI-style explanation text

Good examples:

- `High Value Props`
- `Multi Props Only`
- `Tracking`
- `History`
- `Equal Bet Profit`
- `Actual Profit`
- `Actual ROI`

## Exact Product Behaviors To Preserve

The UI must preserve these Codex-report behaviors:

- top heading: `BetMate Edge: Player Props`
- first visible live section: `High Value Props`
- `Multi Props Only` has extra vertical separation above it
- all visible live rows are `QI 80+`
- live tables sorted by QI descending
- tracking/history sourced from `BetHistory`, not live props
- QI shown as whole numbers
- table columns kept consistent on live tables

## What Base44 Should Not “Improve”

Do not let Base44 automatically convert this into:

- oversized modern KPI cards
- purple-heavy default UI
- chat-style explanations
- accordion-heavy layout
- mobile-first stacked table cards on desktop
- generic SaaS admin design

That would lose the reason this report works.

## Implementation Instruction

Base44 should use this document as a **visual parity spec** in addition to:

- `docs/base44_complete_handover_20260529.md`
- `docs/base44_direct_runtime_transfer_20260529.md`
- `docs/base44_tracking_history_import_package.md`

If Base44 has to choose between:

- generic dashboard best practice
- and matching the current Codex report scan behavior

it should choose matching the current Codex report scan behavior.

