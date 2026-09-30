# College Football Dashboard — To-do list

## Deferred by request

- [ ] **Player targets and target share:** connect enriched passing-play data; count identified intended receivers, exclude throwaways/spikes as appropriate, measure attribution coverage, and publish counts only with a clear coverage label. Never infer targets from receptions. Define the team-target denominator before calculating share.

## Next improvements — proposed, not implemented

- [x] **Adjusted offense:** passing/rushing opponent adjustment and raw/adjusted offensive ranks added to Matchups. Included in this update; awaiting upload and live refresh. Combined matchup scores remain a separate proposed task.
- [ ] **Pace and play volume:** add attempts faced per game and opponent-adjusted yards per attempt/carry to distinguish efficiency from volume.
- [ ] **Player game logs:** allow opening a player’s game-by-game production, opponent, and usage behind window totals.
- [ ] **Sample confidence:** show clearer early-season confidence indicators and opponent-baseline game counts; consider transparent shrinkage toward national averages.
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

Targets stay deferred while the Matchups view is installed.
