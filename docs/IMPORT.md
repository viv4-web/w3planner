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

## Rolled values, sockets and active effects (v32b)
Read from three saves that are kept locally and never committed.
- **Item records** (the player's inventory blob, found by the dye pair `43 00 44 00` / the float `-1.0`): `[name u16] ... [qty u16][durability float][u8 n][n x (u16 name, u32 value, u8)][u16 ref][u16 count x 256][count x u16 ability name][...]`. The extras name only flags and charges (`ammo_current`, `is_initialized`, `ItemDurabilityModified`, `ItemQualityModified`).
- **Rolled values live in the ability list after the extras.** Items made by the game's random generator carry their rolled abilities there as name indices: `autogen_steel_base`, `autogen_steel_dmg` repeated once per damage step, `MA_*` magic abilities (`MA_Armor`, `MA_BurningResistance`, `MA_Vitality`, ...), `quality_masterwork_*` / `quality_magical_*`. The value of each is the ability's number in the game's XML, times the repeat count. The fixed relics and set pieces (Thousand Flowers) list **none**: their numbers are the XML numbers (steel sword 91, silver sword 171 exactly; the tooltip's 82-100 and 154-188 are the game's display range of one hit, the Player Stats screen uses the base). The importer reads the list (`abilities`); an equipped item that has one makes every stat it can change show "-" (its numbers are not decoded: no equipped random item was available to check against the game).
- **Sockets (runestones, glyphs):** the carried `Rune ...` and `Glyph ...` are ordinary inventory records (quantities). No equipped item in these saves has one socketed, so what a socketed item's record looks like was not seen; an item with entries after its extras (the same ability list) is treated like a rolled item, so a socketed rune or glyph can not silently change a number. To learn the layout, a save with one rune in a sword and one glyph in an armour is needed.
- **Active effects:** the player's `effectManager` property holds `W3Effect_*` objects, each a property list: `abilityName` (CName), `duration`, `timeLeft` (seconds, Float). Seen: `ShrineQuenEffect` (Place of Power, +20% Quen Sign intensity, 1800 s), `EnhancedWeaponEffect` (whetstone, +20% attack power, 3600 s), `W3Effect_AutoAirRegen` (no ability). These change Player Stats numbers, and the link cannot hold them: the importer keeps them in memory for the stats screen (`PS.imp.effects`). EnhancedWeaponEffect explained the silver sword's 233 = 171 x 1.2 + 28 (not a roll).
- **Time played:** the one `GameTime` property of type Double (seconds).
