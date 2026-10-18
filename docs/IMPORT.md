# Import save (v31)

Fills the planner from a Witcher 3 **remaster (4.0+) PC** `.sav`. The file is read **in the browser** (File API); it is never uploaded: the page has `connect-src 'none'`, no code path sends bytes anywhere, and the tests fail on any request to another host. Nothing of the importer loads until the dialog opens (the reader is its own hashed script, `src/saveread.js`, plus `data/savenames.json`).

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

## The player's ability list (v32c)
The save holds the player's whole ability list (`stats` > `characterStats` > `value`, an array of CNames; an ability added k times appears k times). It holds no computed Sign power or stamina regeneration, but the numbers are the sum over this list plus the worn items. `src/saveread.js` `abilityList` returns it as `{name: count}`; `src/stats.js` sums it with `STATS.spl` and compares with its own model for an imported build that has not been edited since; a difference shows "—". Details and the abilities the planner does not model: `~/work/w3planner-art/save-spike/FORMAT-NOTES.md` ("The player's ability list and stored stats").

### stats-l9b contributors (v32c)
`AutoSave_106591_7ea48400_52e9569.sav`, NG, level 9, Dol Blathanna set (Armor, Gloves, Pants, Boots), three Greater blue mutagens. Every number below is the game's.

**Sign power of one Sign** (`GetTotalSignSpellPower`, a sum; the Sign intensity total is the mean of the five minus 1):

| Contributor | Source | Amount |
|---|---|---|
| `all_PC_ability` | the player | 1.00 |
| `Lvl2` to `Lvl9` | 3 x 0.02 + 5 x 0.01 | 0.11 |
| `perk_24` x12 | 0.02 x (4 medium pieces x skill level 3); `SetPerkArmorBonus` | 0.24 |
| `greater_mutagen_color_blue_x` x7 | 0.1 each | 0.70 |
| `greater_mutagen_color_blue_synergy_bonus` x30 | 0.016667 each | 0.50 |
| the three Greater blue mutagens' own ability | 0.1 each (modelled, not in the ability list) | 0.30 |
| **Common** | | **2.85** |
| Dol Blathanna Gloves `spell_power_aard` / `spell_power_igni` | items/def_item_armor_dol_blathanna.xml, "Dol Blathanna Gloves _Stats", mult 0.05 (NG+ 0.10) | +0.05 Aard, +0.05 Igni |
| `ShrineQuenEffect` | the save's ability list | +0.20 Quen |

| Sign | Power | Line (game = planner) |
|---|---|---|
| Aard | 2.90 | Stagger 2.90 / 2 - 4 x 0.016 = 139%; Telekinetic damage 0 |
| Igni | 2.90 | Fire damage 100 x 2.90 = 290; Burning (1 + ln 2.90) / 2 - 0.064 = 97% plus the equipped Igni burn-chance skills (`magic_s8`, `magic_s9`), capped at 100% |
| Quen | 3.05 | Physical damage reduction 200 x 3.05 = 610 |
| Yrden | 2.85 | Slowdown 35%; Shock damage 120 x 2.85 = 342; Duration 33.50s |
| Axii | 2.85 | Duration 5 x 2.85 = 14.25s |
| **Total** | (2.90 + 2.90 + 3.05 + 2.85 + 2.85) / 5 = 2.91 | **+191%** |

`stats-l9` (+144%) is the same sum with `perk_24` x12, 2 Greater blue mutagens (`_x` x6, synergy x16) and no Shrine: common 2.4167, Aard and Igni 2.4667, Quen 2.4167.

**Stamina regeneration in combat** (CharacterStatsPopup.ws 322-330): `(add + mult x max Stamina) x (1 + CalculatedArmorStaminaRegenBonus())`, max Stamina 100.

| Contributor | Amount |
|---|---|
| `ConGeralt` | 0.100 |
| `magic_staminaregen` x12 (0.005 each) | 0.060 |
| `perk_24` x12 (0.002 each) | 0.024 |
| mult sum | 0.184, x 100 = 18.4/s |
| `staminaRegen_armor_mod` of the worn pieces: Dol Blathanna Armor 0.10, Gloves, Pants and Boots none | 0.10 |
| 18.4 x (1 + 0.10) | 20.24 |
| shown with `RoundMath` (fraction below .5 rounds down) | **20/s** |

No Glyphword 2, 3 or 4 is in the save's list (they would change the armour bonus, playerWitcher.ws 8685-8725).

## The journal (v33: Quests)
`CJournalManager > JActiveEntries` of the save is the quest journal: `Size` (u32, the number of entries: 927 in `stats-l9b`, 898 in `stats-l9`) and one struct `SJournalEntryStatus` per entry with `path` (one `guid` (CGUID, 16 bytes) + `resource` (String) + `flags` (Uint8) per level, root first), `status` (`EJournalStatus`, a name-table index) and `JEntryUnread` (Bool).
An entry is named by the GUID of the **last** path element; that GUID is the `guid` property of a chunk of a `.journal` file (a quest, a phase, an objective, a description entry ...). States: `JS_Inactive`, `JS_Active`, `JS_Success`, `JS_Failed`. **"Not started" is not a state: the quest has no entry.**
Reader (`journal()` in `src/saveread.js`, no tree building): in the var table (`tb.ents`, [offset, size] sorted) find the `BS` token named `JActiveEntries`, then walk the tokens that follow: `BS SJournalEntryStatus` starts an entry, `BS path` is skipped, `VL guid` (value at +6, 16 bytes) overwrites the entry's GUID (the last one is the entry), `VL status` is a u16 name index, `resource`, `flags`, `JEntryUnread` are skipped; any other token ends the list. Returns `[[guid hex, 'JS_Active'], ...]` in save order (`readSave().journal`, null when the block is missing). Nothing of the journal is read into the link.
The page keeps the entries that are a quest of `data/QUESTS.json` (state of the quest), one of its objectives (state of the objective) or one of its journal entries (`CJournalQuestDescriptionEntry`: present in the save once the game has shown the text; the Quests detail lists only those until the player asks for the whole journal); all 927 / 898 GUIDs of the two fixtures are in the game's journal files, and 46 / 43 of them are quests (`stats-l9b`: 29 done, 15 active, 1 failed, 1 inactive; `stats-l9`: 28, 13, 1, 1). A quest with several active objectives shows all of them; `JTrackedQuest` and `JHighlightedObjective` (`CWitcherJournalManager`) are not read. The `facts` blob (story flags) is not read: its values are not decoded.

## Save version 67 and the sockets tail (v35.2)
- **Record anchor:** records are found by the default-dye pair, which is the pair of NAME-TABLE INDICES of `Dye Default` and `dye_default` in that save (67/68 in the version-66 saves, 147/150 in version 67; the name table differs per save). Until v35.1 the reader had 67/68 hard-coded, so in a version-67 save only the records with durability -1.0 were found (706 of 722) and all six equipped gear pieces were missed ("not found"). v35.2 looks the indices up by name. The four version-66 fixtures read exactly as before (sha1 of the whole result, `tests/test_saveread.js`); `sockets-1` finds all 722 records and imports its gear. A version other than 66 still imports, with the existing "Saved with a game version we haven't tested" notice.
- **Tail of a sword / armour piece** (`gearTail` in `src/saveread.js`; spike notes `~/work/w3planner-art/save-spike/sockets-spike/NOTES.md`): `[u16 ref][u8 nSockets, each: u16 item name, u32 x, u8 nAb, nAb x u16 ability name][u8 nOils, nOils x u16 oil ability][u16 category CName][u16 0]`. **Sockets are imported since v36** (below). Oils (`BeastOil_2`, `CursedOil_2`) are in the same tail and not imported yet.

## Sockets (v36)
- **Reading:** `gearTail` returns the socket item names (`Rune dazhbog`, `Glyph igni lesser`: the same as our ids in `data/socket_ids.json`) with the ability names; the record gets `sockets: [...]` only when the sword or armour piece has one (a save without sockets reads exactly as before: the four version-66 fixtures keep their sha1). `sockets-1`: silver sword = `Rune dazhbog`, chest = `Glyph igni lesser`, nothing else.
- **Matching** (`impPlan`, `src/importsave.js`): by id only. A rune or glyph goes into the build when the planner knows it, it is the right kind for the slot (swords runes, armour glyphs) and the item has room for it (`enhancement_slots` of the ruleset the planner is set to; the save does not say which ruleset it is and NG+ is not read, so the NG / NG+ switch decides). Anything else is listed in the review ("not in planner", "does not fit this slot", "no room in ...") and left out. The review section is "Sockets in your save"; applying it replaces the sockets of the build.
- **Rolled:** an item whose record lists abilities is "rolled" (its numbers unknown, Player Stats shows —) unless every ability is the `<id> _Stats` of a rune or glyph we know (`impRolled`). Anything else, e.g. the `Relic _Stats` that Pyerog, Tvarog and Glyph of Infusion carry, still counts as unknown.
- **Not verified against the game:** `sockets-1` has no sidecar and no Player Stats ground truth; the numbers Player Stats shows for it come from the model (the rune's or glyph's own values added to the item, the way `GetItemAttributeValue` does for the chance lines, `CharacterStatsPopup.ws` 782-863). Runewords and glyphwords are enchantments, not sockets: `RUNEWORDS.md` in the spike folder.
