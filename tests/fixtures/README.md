# Test fixtures

- `tooltips_ref.json`: the text of every skill tooltip at every level (240 texts), captured from the game's own
  formulas. The tooltip test fails if any text changes, so a change to the data or the tooltip code is always deliberate.
  Regenerate it only when the game data itself changed (see docs/DATA-PIPELINE.md).
- `legacy_links.json`: build links made by earlier versions of the planner (v7, v9, v13, v17, v20, v22, v23) together
  with the build each one must open as. Old links must keep opening identically: never break them.
