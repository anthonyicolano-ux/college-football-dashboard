# College Football Dashboard — To-do list

## Deferred by request

- [ ] **Player targets and target share:** connect enriched passing-play data; count identified intended receivers, exclude throwaways/spikes as appropriate, measure attribution coverage, and publish counts only with a clear coverage label. Never infer targets from receptions. Define the team-target denominator before calculating share.

## Next improvements — proposed, not implemented

- [x] **Adjusted offense:** passing/rushing opponent adjustment and raw/adjusted offensive ranks added to Matchups. Installed and confirmed working.
- [x] **Volume and efficiency:** attempts/game, attempts versus opponent baseline, adjusted yards per attempt/carry and efficiency ranks installed and confirmed working. True plays/minute remains unimplemented.
- [x] **Player game logs and recent form:** included in this update; requires upload and refresh. Links from Player Stats and Matchups, per-game production/usage, and Season/Last 3/Last Game comparisons with recorded-game coverage.
- [x] **Sample indicators:** minimum opponent baseline games and usable efficiency games included in the current update.
- [ ] **Sample confidence model:** consider transparent shrinkage toward national averages and validate calibration before publishing confidence scores.
- [ ] **Stat completeness:** audit TD, interception and player-category gaps; show field coverage rather than treating missing categories as zero. Distinguish confirmed appearances from games with recorded offensive stats if a reliable source exists.
- [ ] **Refresh efficiency:** share private fetched inputs across the updaters and cache unchanged games to reduce API quota use, while periodically rechecking source corrections.
- [ ] **Data freshness:** expose the latest refresh attempt separately from the last successful publication, plus visibly stale-data indicators.
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
- **Operational bundle — proposed:** reduce duplicate API calls, cache/recheck source corrections, and expose refresh failures/stale data together.
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
