# Import save (v31)

Fills the planner from a Witcher 3 **Next-Gen (4.0+) PC** `.sav`. The file is read **in the browser** (File API); it is never uploaded: the page has `connect-src 'none'`, no code path sends bytes anywhere, and the tests fail on any request to another host. Nothing of the importer loads until the dialog opens (the reader is its own hashed script, `src/saveread.js`, plus `data/savenames.json`).

## What it reads (v1 scope) and what it does with it
| Section | From the save | Goes into |
|---|---|---|
| Character | level, XP, skill points used/free; every learned skill (level) and the equipped skill slots | the build link: Level, Bonus points (= points in the save - (level - 1)), skill levels, slots 1-8 |
| Mutagens | the four skill-mutagen slots | the link: our mutagen index, from the save item id (`data/SAVEMUT.json`) |
| Equipment | steel and silver sword, chest, gloves, trousers, boots, crossbow, bolts, mask | the link, `g1`: the item whose id equals the save id, in the current ruleset |
| Consumables | Potion 1-4, Bomb 1-2 (charges `ammo_current`) | the link, `c1` positions 0-5; the oil positions are left as they are |
| Stash | every inventory record the planner knows (gear and consumables, with quantities) + crowns | `localStorage['w3planner.stash']` only; **never in the link** |
Each section has a tick box; Apply writes only the ticked ones, through the planner's own state (`enforceLocks`, `save()`), and lands on Character. The link format is unchanged (no new field; old links byte-identical).

## Not read in this version (the dialog says so)
Active mutation and researched mutations (the reader sees them but only the "none researched" case was ever tested), oils on swords (not located in the save), NG vs NG+ (no marker found; the planner's ruleset stays), and any item the planner does not plan (a quest item in the Pocket, a second bomb or Pocket slot).

## Matching rules (decisions)
- **By id only.** Save item and skill names are the game's internal ids = our item and skill ids. Never by display name, never by icon. Display names collide ("Bolts" is `Bodkin Bolt` and `Harpoon Bolt`).
- **Our localised names only.** The dialog shows `items_*.json` / `consumables.json` / skill names. Items the planner does not plan are named from `data/savenames.json` (food and drink that is not in a slot, quest items).
- **Food and the Pocket are consumables.** The four potion slots take potions, decoctions, food and drink (the game's `GetSlotForItem`: tags `Potion`, `Edibles`, `Drinks`), the Pocket takes the save's `Quickslot1` item (a Torch, an Oil Lamp). They are matched by id like any consumable (`Cows milk` ×30, `Bottled water` ×66 fill their slots). What the planner cannot hold (an unknown id, a quest item, a second bomb or Pocket slot) is listed "(not in planner) - slot left empty", never dropped silently.
- **Unknown or mod ids** are listed "not imported", never fuzzy-matched.
- **Skill mutagens**: `tools/make_save_data.py` builds `SAVEMUT.json` once from the game's item XML + `en.w3strings` (e.g. `Gryphon mutagen` -> our Griffin, `Fogling 1 mutagen` -> Foglet, `Czart mutagen` -> Chort); 36 ids, one per planner mutagen.

## Version and mod warnings
The `.json` next to a save (drop it too) has the build id, `gameVersion`, `saveVersion`, platform and the mod list: the review shows the build and, with mods, "This save lists N mods (names). Items or skills added by mods are skipped." Without the sidecar the header codes (66, 29, 164) are used. Tested: save version 66, game version 29 (5.0.x). Anything else: "Saved with a game version we haven't tested. We'll try; check the results."

## Format (our own reader; MIT; written from FORMAT-NOTES.md of the spike and tests on one reference save)
Container `SNFH` `FZLC`: i32 chunk count, i32 header size, per chunk (compressed, decompressed, end offset), LZ4 blocks of 1 MiB. Tail `SE`; name table `NM`/`MANU`; variable table; the player is the `SS` blob that holds the `levelManager` property; its `Entity` block has PORPs `levelManager`, `abilityManager`, `itemSlots`; the inventory is a raw binary list after the entity's blocks. Details: `src/saveread.js` comments. A new game patch may change the header codes or layout: that is the main risk (hence the warning).

## Tests
`tests/test_saveread.js` (node: LZ4 vectors, header and truncation errors, sidecar incl. repeated `mod` keys, the mutagen table, savenames, and the reference save if present), `tests/importcheck.py` (browser: button on every tab, dialog texts, lazy load, Escape, bad-file errors, food/unknown/mod rules on a synthetic result, the phone flow, offline has no button; and with the local reference save in `~/work/w3planner-art/save-spike/fixtures/refsave/` the whole acceptance list, Apply and the link round trip). The save, its .png/.json and the ground truth are **never committed**.
