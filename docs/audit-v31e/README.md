# v31e: ruleset audit (NG / NG+)

Made by `python tools/audit_rulesets.py --game-dir ~/incoming/gamedata --levels` from the game's XML (re-extracted from the bundles). Every table has one row per id, level and ruleset:
planner (what the build shows), XML (what the game's own data gives), status. A row that was wrong in production before the audit says `fixed` below; the TSV files hold the state after the fix (all `ok`).

| File | Rows | Area |
|---|---|---|
| `skills.tsv` | 480 | every skill (80) at 1/3, 2/3, 3/3 in NG and NG+: tooltip text |
| `skill_abilities.tsv` | 350 | the ability values behind them (175 attributes per ruleset) |
| `items.tsv` | 1064 | every item of both lists (422 NG, 642 NG+): stat numbers |
| `consumables.tsv` | 252 | 126 potions, decoctions, bombs and oils per ruleset: toxicity, duration, charges, effect numbers |
| `mutagens.tsv` | 18 | the nine regular mutagens |
| `mutations.tsv` | 24 | the 12 mutations: research costs |

Set bonuses: not a table. `tools/extract_items.py` stops if a set bonus differs between the rulesets, and none does. Mutation and mutagen XML is identical in both.

## What was wrong (status `fixed`)
Production v31 read every ability value from `gameplay/abilities_plus` (NG+). v31d switched it to NG, which fixed NG and, as a side effect, made NG+ show NG numbers. v31e keeps both.

| id | name | level | ruleset | production v31 | v31d | v31e (= XML) | status |
|---|---|---|---|---|---|---|---|
| alchemy_s10 | Pyrotechnics | 1/3, 2/3, 3/3 | NG | 100, 200, 300 | 50, 100, 150 | 50, 100, 150 | fixed in v31d |
| alchemy_s10 | Pyrotechnics | 1/3, 2/3, 3/3 | NG+ | 100, 200, 300 | 50, 100, 150 (wrong) | 100, 200, 300 | fixed |
| alchemy_s3 | Delayed Recovery | 1/3, 2/3, 3/3 | NG | "?%" | 70%, 65%, 55% | 70%, 65%, 55% | fixed in v31d |
| alchemy_s3 | Delayed Recovery | 1/3, 2/3, 3/3 | NG+ | "?%" | 70%, 65%, 55% (wrong) | 0% (see below) | fixed |
| alchemy_s11 | Cluster Bombs | 1/3 to 3/3 | both | text has no damage number | - | text unchanged; data NG 200/200/50, NG+ 400/400/100 | ok (not shown) |

Everything else matched in both rulesets: the other 77 skills have the same ability values in NG and NG+, so they stay shared.

## Notes that need a look in the game
- **NG+ Delayed Recovery.** The NG+ XML defines only `toxicity_threshold` (0.15). The scripts (`GetAlchemyS03Threshold`, playerWitcher.ws) read only `toxicity_threshold_lvl1` to `lvl3`, which NG+ does not define, so the formula gives 0 and the tooltip says "above 0%". Shown as the game's own formula gives it; please check it in an NG+ game.
- **Basilisk decoction** (`Mutagen 23`) lists `duration` twice in both rulesets (1800 and 3960). The planner shows 3960 (as before); not ruleset related; unverified.
- **Player Stats (v32 branch, not in main).** `STATS.json` already has per-ruleset level tables and base stats. Its active-effect numbers (`eff`: Full Moon, Swallow, White Raffard's decoction, Pheromone) are read from NG only; NG+ differs (Full Moon +300/650/1000 in NG, +600/1100/1500 in NG+; White Raffard's +35%/60% vs +60%/80%). To be made per ruleset when v32 is merged.
