# College Football Dashboard — To-do list

## Sharing permission — awaiting Tony’s follow-up

- [ ] **Ask CFBD about public season-wide player game logs.** Keep this open until their reply is recorded. The current public players.json contains normalized individual game records; reasonable display versus bulk redistribution remains unresolved. This item is not a legal clearance.

Question to send or revisit:

> I built a college football dashboard using your API. It displays team aggregates, derived matchup rankings, player averages, and individual player game logs. GitHub Pages serves the dashboard from public JSON files, including one containing the season’s player logs. The API key and original API responses remain private. Is publishing those normalized game-log records permitted, or should they remain private and be served only in limited player-specific views?

- [ ] Record CFBD’s response here, including date and any publication conditions.
- [ ] If permission is not granted or remains unclear, revise data publication before recommending broad sharing. Removing a page link alone would not remove a publicly accessible dataset or its repository history.


## Deferred by request

- [ ] **Player targets and target share:** connect enriched passing-play data; count identified intended receivers, exclude throwaways/spikes as appropriate, measure attribution coverage, and publish counts only with a clear coverage label. Never infer targets from receptions. Define the team-target denominator before calculating share.

## Next improvements — proposed, not implemented

- [x] **Adjusted offense:** passing/rushing opponent adjustment and raw/adjusted offensive ranks added to Matchups. Installed and confirmed working.
- [x] **Volume and efficiency:** attempts/game, attempts versus opponent baseline, adjusted yards per attempt/carry and efficiency ranks installed and confirmed working. True plays/minute remains unimplemented.
- [x] **Player game logs and recent form:** included in this update; requires upload and refresh. Links from Player Stats and Matchups, per-game production/usage, and Season/Last 3/Last Game comparisons with recorded-game coverage.
- [x] **Sample indicators:** minimum opponent baseline games and usable efficiency games included in the current update.
- [ ] **Sample confidence model:** consider transparent shrinkage toward national averages and validate calibration before publishing confidence scores.
- [x] **Stat completeness indicators:** reported-game counts for team and player fields included in this update; missing values remain unavailable.
- [ ] **Appearance confirmation:** distinguish actual appearances from recorded offensive-stat games only if a reliable source becomes available.
- [x] **Refresh efficiency:** share API responses privately within one refresh. Fetch every source again on each run to pick up corrections. Included in this update; awaiting installation.
- [ ] **Persistent game caching:** consider only after defining a source-correction recheck policy; not implemented.
- [x] **Data freshness:** latest published attempt, last validated refresh, per-page dataset times and 108-hour stale warning included in this update. Cancelled runs or failed status publication may remain absent.
- [ ] **All-opponents option:** add FCS-inclusive raw results as a separately labeled view. Keep opponent-adjusted comparisons within a clearly defined eligible population.
- [ ] **Home/away and conference splits:** introduce additional windows after core comparisons are validated.
- [ ] **Injuries and roster changes:** investigate a reliable, permitted source before displaying availability indicators.
- [ ] **Snap counts:** optional only; add if a reliable source and appropriate rights are found.
- [ ] **Matchup ratings/projections:** backtest and document calibration before labeling a combined matchup favorable/neutral/difficult or predicting player output. Current Matchups labels describe opposing defense only.

## Delivered before this update

- [x] Team Defense: raw, adjusted and compare ranks; pass/rush and game-window filters.
- [x] Player Stats: QB/RB/WR/TE tables; production and carry/reception shares.

## Included in this update — awaiting upload and first live schedule validation

- [x] Matchups page connecting offensive players with opposing defensive metrics.
- [x] Upcoming-game selector, either-team offense selection and manual team comparison.
- [x] Schedule updater and workflow integration.

Targets remain deferred by request.

## Suggested implementation bundles

- **Current bundle — volume, efficiency and sample indicators:** shared game inputs, no extra API requests; included in this update, awaiting upload/live refresh.
- **Receiving usage bundle — deferred:** targets, target share and receiver attribution coverage should be developed together after enriched passing data is validated.
- **Player detail bundle — proposed:** game logs and recent-form summaries can share one player-history view.
- **Operational bundle — included:** reduce duplicate requests within each refresh, recheck all source inputs on each run, stage the dataset set before publication, and expose published refresh results/stale data.
- **Modeling bundle — separate:** shrinkage, combined matchup ratings and projections require backtesting/calibration before release.
- **New-source work — separate:** injuries and optional snap counts need their own coverage and rights checks.

Bundling reduces repeated integration work; it does not guarantee a bug-free release. Each bundle should retain calculation and source-coverage checks.


## Weekly matchup screen — included in this update

- [x] Passing and rushing weekly rankings from the existing validated datasets.
- [x] Balanced and efficiency-first weighting, score breakdowns, sample filters, and alternate-view ranks.
- [x] Links that open the exact game and offensive side in Matchups.
- [ ] Historical backtesting of the descriptive score before any predictive labels or projections.
- [ ] Player game logs and recent-form summaries remain the next proposed feature bundle.


## Player history bundle — included in this update

- [x] Derived player logs published in existing players.json; no additional API requests.
- [x] Player detail page, name links, recent window summaries, and explicit no-recorded-stats rows.
- [ ] Targets remain deferred by request.


## Refresh operations bundle — included in this update

- [x] Stage all three datasets; publish them in one commit only after all validators pass.
- [x] Publish a small failure status without replacing validated datasets.
- [x] Shared freshness/status banner on all five dashboard pages.
- [ ] Persistent cross-run caching remains deferred; no raw API responses or credentials are stored publicly.


## Coverage and operational follow-up — included in this update

- [x] Field coverage on Team Defense, Player Stats, Matchups cards/player table, and Player Logs recent-form summaries.
- [x] Actual API request-attempt counts, including retries, with partial tracked UTC-month totals in the refresh banner. No API keys or raw responses enter the usage log.
- [x] Player Logs navigation is consistent across all five pages; navigation wraps on narrow screens.
- [ ] Check rendered layouts on a phone and a second browser; no browser visual QA was available locally.
- [ ] Compare tracked requests with the official CFBD account counter. Earlier runs, other projects and unpublished statuses are outside this tracker.
- [ ] Historical matchup backtesting and weighting sensitivity remain proposed; no predictive calibration is claimed.
- [ ] Targets and target share remain deferred by request.
