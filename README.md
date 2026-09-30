# College Football Dashboard

Team Defense V1: pass/rush defense, Raw / Adjusted / Compare views, Season / Last 3 / Last Game, conference and team filters. This project is separate from the NFL dashboard.

## First setup

1. Add your CFBD key under **Settings → Secrets and variables → Actions → New repository secret**, named `CFBD_API_KEY`. Never add it to a file or share it in chat.
2. Open **Actions → Update college football data → Run workflow**. Leave the year at 2026 and run on `main`.
3. Wait for a green check. On failure, open the failed step for the reason. No data file is replaced or committed by a failed refresh.
4. Enable **Settings → Pages → Deploy from a branch → main → / (root) → Save**.
5. Open https://anthonyicolano-ux.github.io/college-football-dashboard/ after Pages finishes publishing.

The workflow refreshes on Sundays, Mondays and Fridays at 12:23 UTC (7:23 AM Central during daylight saving time; 6:23 AM during standard time). GitHub schedules can run late. Requests use 2 metadata calls plus one call per completed week/season type. It currently refreshes the whole season so provider corrections are included. Quota depends on season length and CFBD access; if quota is exhausted, the workflow fails safely. Update the default season in the workflow for a future year.

## Methodology

Only completed FBS-versus-FBS games count. Games against FCS opponents are excluded. All FBS teams are listed, including teams with no eligible games (unranked). Last 3 means the last three eligible games, not weeks.

Raw rank uses yards allowed per game, ascending. Completion and efficiency metrics use combined totals. Points allowed includes opponent scoring from all phases. Source NCAA rushing conventions may include sacks.

For each game, expected yards are the opponent's mean offensive yards in its **other** eligible games through the dataset cutoff. Adjusted % = total actual / total expected × 100, using the same usable games. Below 100% means fewer yards allowed than expected. Adjusted ranks require baseline coverage for every selected game; partial comparisons remain visible but unranked. Compare ranks raw and adjusted performance within the same adjusted-eligible pool, so its raw rank can differ from the main Raw view. Positive rank change = improvement. Ties share a rank. Small samples are not predictive certainty; this is opponent-production adjustment, not a complete schedule/pace/game-script model.

TD and interception categories are optional until verified against live responses; missing values display as —. The updater strictly requires valid yards, attempts and pass completions. It rejects missing game box scores, participant mismatches, duplicate games and regressions in completed-game coverage. All transformations complete before an atomic file replacement. Public JSON contains only display aggregates, not raw API responses.

## Data and security

Data: [CollegeFootballData](https://collegefootballdata.com/). Dashboard rankings and adjustments are our calculations. Follow [provider terms](https://collegefootballdata.com/terms). Credentials run only inside GitHub Actions; the browser only fetches `data/teams.json`. No raw API responses are committed. No data is fabricated when the first refresh has not run.

## Validation and scope

Run `python -m unittest discover -s tests -v`. Local tests use synthetic box scores; authenticated live response validation occurs in the first workflow run. Player stats, targets, upcoming opponents and matchup views are future slices and are not yet populated. Snap counts are optional.
