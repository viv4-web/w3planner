# Data pipeline: from game files to `data/*`

The planner's numbers, names and descriptions come from the game's own files, not from a wiki. This page says what each data file holds, where it came from, and what is and is not scripted yet.

**Status, honestly:** the extraction was done interactively, step by step. The low-level tools are saved as scripts in `tools/extract/`. The steps that turn game XML into the JSON files below were run by hand and are **not yet scripted**. The first job for whoever next has the game files is to write `tools/extract/build_data.py` and check that it regenerates the current files exactly (`git diff` shows nothing).

## Tools in `tools/extract/`
| Script | Does |
|---|---|
| `w3dec.py` | decodes `en.w3strings` (v164; UTF-8 since the remaster) into id to text |
| `w3tex.py` | extracts textures (icons) from `texture.cache` |
| `swfimg.py` | extracts the images embedded in the Flash menu files (`panel_character_dupe.swf` and friends) |
| `tr.py` | translates the game's tooltip code (`characterMenu.ws`, `characterMenuDupe.ws`) into JavaScript |
| `rt.js` | the helper functions (`SA`, `AA`, `MUL`, `CALC`, `NTZ`, `FTS`, `LOC`...) that the translated tooltip functions call; the same helpers live inside `src/app.js` |

## Data files
| File | Holds | Source in the game files |
|---|---|---|
| `DATA.json` | 80 skills in 4 trees: `[id, name, gridRow, gridCol, maxLevel, points, prerequisites[], alternative, reward, ability]` | `geralt_skills.xml` (the `abilities_plus` copy wins over `abilities`) |
| `EXTRA.json` | per skill: display name, description, icon slot | strings (`en.w3strings`) plus icon paths in the skill XML |
| `TIPDATA.json` | `ab` (ability attribute values), `locs` (attribute names), `desc` (per-level descriptions with placeholders) | ability XML files, strings |
| `TIPFN.js` | 79 compiled tooltip functions | translated from the game's menu scripts by `tr.py` |
| `MUT.json`, `MASTER.json` | the 12 mutations and the master mutation: costs, prerequisites, colours, descriptions | `bob_abilities/abilities_plus/geralt_mutations.xml`; description numbers from `effects_ep2.xml` and `playerWitcher.ws` |
| `MUTS.json` | the 9 regular mutagens (red, blue, green; lesser, regular, greater) and their bonuses | ability definitions and items in `def_item_ingredients.xml` |
| `SPECIAL_MUT.json` | the 27 special (monster) mutagens, 9 per colour, `[label, colour]` | items tagged `MutagenIngredient` with `mod_alchemy_table` in `def_item_ingredients.xml`; all use the lesser ability, so they give the lesser bonus |
| `SPECIAL_MUT_ICONS.json` | for each special mutagen: its game item (`Mutagen N`), its own icon file (original and sanitised name), how it was matched, and its art slot token. File names only | `def_item_alchemy_mutagens.xml` (`icon_path` of each item) plus the icon files, joined by `tools/map_special_icons.py` (the XML has no display names, so see that tool for how labels are matched) |
| `ART.json`, `GA.json`, `MUTIMG.json`, `LOCK.js` | only art slot tokens (`@@img:...@@`), resolved at build time | see `art/manifest.json` |

Unlock thresholds come from `geralt_skills.xml` too: 12 skill slots at total skill points 0, 2, 4, 6, 8, 10, 12, 15, 18, 22, 26, 30; 4 mutagen sockets at 2, 9, 16, 28; 4 mutation slots after 2, 4, 8 and 12 researched mutations. Skill slots and sockets unlock by total points (level minus one plus bonus points), not by level.

## Known limits of the data
- A few tooltip values depend on live stats or gear (for example crossbow damage), so they show `?` or the base value.
- Older guides quote special mutagen bonuses of +10% or +150; the current game data says they equal the lesser mutagen.
- The game's "required points spent in this tree" gates on skills are not enforced yet; only prerequisites are.

## Art
Icons come from `texture.cache` (`w3tex.py`); menu art (tile backgrounds, frames, tab icons, mutation cells) from the Flash file images (`swfimg.py`). The live build needs these in `~/work/w3planner-art/<slot id>.<ext>`; see `art/manifest.json` for the slot ids and `CLAUDE.md` for how to add one.
