# Test fixtures

- `tooltips_ref.json`: the text of every skill tooltip at every level (240 texts), captured from the game's own
  formulas. The tooltip test fails if any text changes, so a change to the data or the tooltip code is always deliberate.
  Regenerate it only when the game data itself changed (see docs/DATA-PIPELINE.md).
- `legacy_links.json`: build links made by earlier versions of the planner (v7, v9, v13, v17, v20, v22, v23) together
  with the build each one must open as. Old links must keep opening identically: never break them.
- `links/<version>.txt` and `links/<version>.json`: links made by that version's own code (v24 and later), one per line, and for each the
  build it must open as (name, level, bonus points, skill levels, slots, mutagens, researched mutations, active mutation). They cover every
  tree, every mutation, all 27 special mutagens, levels 1 and 100, an empty build and a full build. Made with `tools/make_link_fixtures.py`,
  which never overwrites. Append-only: `tests/linkcheck.py` compares them with `main` and fails if any link or expectation was edited or removed.
- `links/v27.txt` and `v27.json`: 25 links that carry the gear segment `g1` (every slot alone in both modes, full sets, mixed, the highest item numbers, skills + mutagens + gear, no gear). Their expected state has `gear` (9 registry numbers) and `ruleset`.
