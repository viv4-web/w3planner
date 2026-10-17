#!/usr/bin/env python3
"""The numbers behind the Player Stats screen (v32): data/STATS.json, from the game's ability XML (gameplay/abilities and gameplay/abilities_plus in xml.bundle).

    python tools/make_stats.py --bundle ~/incoming/gamedata/bundles/xml.bundle

lvl      per level 2..: [vitality base, attack_power add, spell_power mult] from the abilities Lvl2..LvlN (geralt_stats.xml), one table per ruleset (abilities = ng, abilities_plus = ng_plus)
con      the base character ability ConGeralt (geralt_stats.xml): vitality, stamina, toxicity, critical hit chance and damage, poison and bleeding resistance
surv     the skills that add 1% Vitality per level while equipped (PlayerAbilityManager.ws 162-186: perk path, isReworked or isUnchangedLegacy); `survival_vitality` has vitality mult 0.01
touch    skill id -> the watched attributes its ability changes (a skill that changes a stat the screen does not model makes that stat show "—")
syn      the Synergy step (perk_43 synergy_bonus, 0.1 per level)
spl      per ability name: its spell_power (mult, all Signs) and per-Sign spell_power_<sign>, and staminaRegen (mult): what the player's own ability list (the save's `characterStats`) is summed with (v32c)
mods     per skill that has modifier_tags (the five Signs' own skills and a few more): the skills whose ability carries one of those tags (GetSkillAttributeValue adds them x level: PlayerAbilityManager.ws PrecacheModifierSkills)
sgn      the Signs skills that give `magic_staminaregen` x level while equipped (reworked or unchanged legacy, not core: PlayerAbilityManager.ws AddSkillPassiveBonusesForEquipped)
armor_type  item id (both rulesets; equal where an id is in both) -> light | medium | heavy (the item tags LightArmor, MediumArmor, HeavyArmor: inventoryComponent.ws GetArmorType) for the four armour slots
eff, touch, eff_names, mods   NG, and `effp`, `touchp`, `eff_namesp`: for each name whose NG+ record differs, the NG+ record (null = not in NG+); v31e: both rulesets are read with tools/audit_rulesets.py's
                        reader (a _plus file replaces the base file), and syn, surv, surv_mult must be equal in both or this tool stops
"""
import argparse, json, re, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WATCH = re.compile(r"^(vitality.*|stamina.*|toxicity|armor|attack_power.*|critical_hit.*|spell_power.*|instant_kill.*|.*resistance.*|.*[Rr]egen.*)$")


# the game's own words (en.w3strings), by the keys CharacterStatsPopup.ws uses
LABELS = """panel_common_statistics_tooltip_silver_dps panel_common_statistics_tooltip_steel_dps attribute_name_armor item_category_crossbow vitality attribute_name_toxicity stat_signs stamina panel_common_statistics_category_additional
panel_common_statistics_tooltip_silver_fast_dps panel_common_statistics_tooltip_silver_fast_crit_chance panel_common_statistics_tooltip_silver_fast_crit_dmg panel_common_statistics_tooltip_silver_strong_dps panel_common_statistics_tooltip_silver_strong_crit_chance panel_common_statistics_tooltip_silver_strong_crit_dmg
panel_common_statistics_tooltip_steel_fast_dps panel_common_statistics_tooltip_steel_fast_crit_chance panel_common_statistics_tooltip_steel_fast_crit_dmg panel_common_statistics_tooltip_steel_strong_dps panel_common_statistics_tooltip_steel_strong_crit_chance panel_common_statistics_tooltip_steel_strong_crit_dmg
attribute_name_desc_poinsonchance_mult attribute_name_desc_bleedingchance_mult attribute_name_desc_burningchance_mult attribute_name_desc_confusionchance_mult attribute_name_desc_freezingchance_mult attribute_name_desc_staggerchance_mult
slashing_resistance_perc attribute_name_piercing_resistance_perc bludgeoning_resistance_perc attribute_name_rending_resistance_perc attribute_name_elemental_resistance_perc attribute_name_poison_resistance_perc attribute_name_bleeding_resistance_perc attribute_name_burning_resistance_perc
panel_common_statistics_tooltip_crossbow_crit_chance attribute_name_piercingdamage attribute_name_silverdamage attribute_name_bludgeoningdamage attribute_name_firedamage
panel_common_statistics_tooltip_outofcombat_regen panel_common_statistics_tooltip_incombat_regen toxicity_offset toxicity
Aard attribute_name_knockdown attribute_name_forcedamage Igni effect_burning Quen physical_resistance Yrden SlowdownEffect ShockDamage duration Axii
attribute_name_staminaregen_out_of_combat attribute_name_staminaregen per_second bonus_herb_chance instant_kill_chance human_exp_bonus_when_fatal nonhuman_exp_bonus_when_fatal""".split()


def text(path):
    return re.sub(r"<!--.*?-->", "", Path(path).read_text(encoding="utf-8-sig"), flags=re.S)


class Ab:
    """One ability: children = [(tag, {attr: value})] (read by tools/audit_rulesets.abilities_in: regular expressions, because the game's XML repeats attributes on some tags)"""
    def __init__(self, children):
        self.children = children


def attr(a, name):
    """[(type, min)] of an attribute element"""
    return [(c.get("type") or "base", float(c["min"])) for tag, c in a.children if tag == name and "min" in c]


SIGNS = ("aard", "igni", "yrden", "quen", "axii")


def tags_of(txt):
    """{ability: [tags]}: the text of <tags> inside each <ability> block (a self-closing <ability .../> has none)"""
    out = {}
    for m in re.finditer(r'<ability\s+name\s*=\s*"([^"]+)"[^>]*?(?<!/)>(.*?)</ability>', txt, re.S):
        t = re.search(r"<tags>(.*?)</tags>", m.group(2), re.S)
        out[m.group(1)] = [x.strip(' "\t\r\n') for x in t.group(1).replace("\n", " ").split(",") if x.strip(' "\t\r\n')] if t else []
    return out


def skill_defs(txt):
    """{skill: {"mod": [modifier_tags], "path": pathType_name, "core": bool, "rw": isReworked or isUnchangedLegacy}}"""
    out = {}
    for m in re.finditer(r"<skill\s([^>]*?)(?<!/)>(.*?)</skill>", txt, re.S):
        at = dict(re.findall(r'(\w+)\s*=\s*"([^"]*)"', m.group(1)))
        if not at.get("skill_name"): continue
        mt = re.search(r"<modifier_tags>(.*?)</modifier_tags>", m.group(2), re.S)
        out[at["skill_name"]] = {"mod": [x.strip(' "\t\r\n') for x in re.split(r"[,\s]+", mt.group(1)) if x.strip(' "\t\r\n')] if mt else [], "path": at.get("pathType_name"),
                                 "core": at.get("isCoreSkill") == "1", "rw": at.get("isReworked") == "1" or at.get("isUnchangedLegacy") == "1"}
    for m in re.finditer(r"<skill\s([^>]*?)/>", txt):                       # self-closing skills (no modifier tags)
        at = dict(re.findall(r'(\w+)\s*=\s*"([^"]*)"', m.group(1)))
        if at.get("skill_name") and at["skill_name"] not in out:
            out[at["skill_name"]] = {"mod": [], "path": at.get("pathType_name"), "core": at.get("isCoreSkill") == "1", "rw": at.get("isReworked") == "1" or at.get("isUnchangedLegacy") == "1"}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); ap.add_argument("--bundle", help="unused since v31e (the game files are read from --game-dir)"); ap.add_argument("--game-dir", default=str(Path.home() / "incoming" / "gamedata")); a = ap.parse_args()
    sys.path.insert(0, str(ROOT / "tools")); sys.path.insert(0, str(ROOT / "tools" / "extract")); import audit_rulesets as AR, extract_items as EI, w3dec
    strs, keys = w3dec.decode(str(Path(a.game_dir) / "en.w3strings")); games = {rs: EI.Game(a.game_dir, rs, (strs, keys)) for rs in AR.RULESETS}

    def abil(g, names):
        out = {}
        for k, blob in AR.files_of(g, "abilities", names):
            if k[0] == "xml.bundle":                      # the base game, as before (the DLC packages hold no player stats)
                for n, kids in AR.abilities_in(AR.text_of(blob)).items(): out[n] = Ab(kids)
        return out

    def watched(ab, only=None):
        return {n: sorted({tag for tag, _ in e.children if tag != "tags" and WATCH.match(tag)}) for n, e in ab.items() if (only is None or only(n))}

    R = {}
    for rs, g in games.items():
        r = R[rs] = {}
        st = abil(g, ("geralt_stats.xml",)); rows = []
        for n in range(2, 101):
            ab = st.get("Lvl%d" % n)
            if ab is None: break
            gg = lambda k, t: sum(v for ty, v in attr(ab, k) if ty == t)
            rows.append([gg("vitality", "base"), gg("attack_power", "add"), round(gg("spell_power", "mult"), 6)])
        r["lvl"] = rows
        con = st["ConGeralt"]; c = lambda k, t="base": next((v for ty, v in attr(con, k) if ty == t), 0)
        r["con"] = {"vitality": c("vitality"), "stamina": c("stamina"), "toxicity": c("toxicity"), "crit_chance": c("critical_hit_chance"), "crit_damage": c("critical_hit_damage_bonus", "add"),
                    "poison_resist": c("poison_resistance_perc"), "bleeding_resist": c("bleeding_resistance_perc"),
                    "vit_regen": c("vitalityRegen", "add"), "vit_combat_regen": c("vitalityCombatRegen", "add"), "stamina_ooc_mult": c("staminaOutOfCombatRegen", "mult")}
        ab = abil(g, ("geralt_skills.xml",)); sk = "".join(AR.text_of(b) for k, b in AR.files_of(g, "abilities", ("geralt_skills.xml",)) if k[0] == "xml.bundle")
        r["syn"] = attr(ab["perk_43"], "synergy_bonus")[0][1]; r["surv_mult"] = attr(ab["survival_vitality"], "vitality")[0][1]; r["surv"] = []
        for m in re.finditer(r"<skill\s([^>]*)>", sk):
            at = dict(re.findall(r'(\w+)\s*=\s*"([^"]*)"', m.group(1))); n = at.get("skill_name")
            if n and n.startswith("perk_") and (at.get("isReworked") == "1" or at.get("isUnchangedLegacy") == "1"): r["surv"].append(n)
        r["touch"] = {n: v for n, v in watched(ab, lambda n: re.match(r"^(sword|magic|alchemy|perk)_", n) or n.startswith("mutation")).items() if v}
        # v32c: what the Sign intensity and the Stamina regeneration lines are made of
        sktxt = "".join(AR.text_of(b) for k, b in AR.files_of(g, "abilities", ("geralt_skills.xml",)) if k[0] == "xml.bundle"); sd = skill_defs(sktxt); tg = tags_of(sktxt)
        r["mods"] = {sk: sorted(o for o in sd if o != sk and any(t in tg.get(o, []) for t in d["mod"])) for sk, d in sd.items() if d["mod"]}
        r["mods"] = {k: v for k, v in r["mods"].items() if v}
        r["sgn"] = sorted(k for k, d in sd.items() if d["path"] == "Signs" and d["rw"] and not d["core"])
        sp_ab = {}
        for fn in ("geralt_skills.xml", "geralt_stats.xml", "common_abilities.xml", "effects.xml", "effects_potions.xml", "effects_mutagens.xml", "misc.xml"):
            sp_ab.update(abil(g, (fn,)))
        for k, blob in AR.files_of(g, "items", ("def_item_ingredients",)):
            for n, kids in AR.abilities_in(AR.text_of(blob)).items(): sp_ab[n] = Ab(kids)
        spl = {}
        for n, e in sp_ab.items():
            rec = {}
            for key, out_key in [("spell_power", "sp")] + [("spell_power_" + x, x) for x in SIGNS] + [("staminaRegen", "sr")]:
                v = round(sum(val for ty, val in attr(e, key) if ty == "mult"), 6)
                if v: rec[out_key] = v
            if rec: spl[n] = rec
        r["spl"] = spl
        r["armor_type"] = {}
        for it in json.loads((ROOT / "data" / ("items_ng.json" if rs == "ng" else "items_ng_plus.json")).read_text())["items"]:
            if it["slot"] not in ("chest", "gloves", "trousers", "boots"): continue
            r["armor_type"][it["id"]] = None
        for k, blob in AR.files_of(g, "items"):
            txt = AR.text_of(blob); starts = list(re.finditer(r'<item\s+name\s*=\s*"([^"]+)"', txt))
            for i, m in enumerate(starts):
                if m.group(1) in r["armor_type"]:
                    body = txt[m.end(): starts[i + 1].start() if i + 1 < len(starts) else len(txt)]; t = re.search(r"<tags>(.*?)</tags>", body, re.S)
                    tl = [x.strip() for x in t.group(1).replace("\n", " ").split(",")] if t else []
                    r["armor_type"][m.group(1)] = "light" if "LightArmor" in tl else "medium" if "MediumArmor" in tl else "heavy" if "HeavyArmor" in tl else None
        r["armor_type"] = {k: v for k, v in r["armor_type"].items() if v}
        r["eff"] = {}; r["eff_names"] = {}
        for f in ("effects.xml", "effects_potions.xml", "effects_mutagens.xml", "misc.xml", "weather_abl.xml"):
            for n, e in abil(g, (f,)).items():
                names = sorted({tag for tag, _ in e.children if tag != "tags" and WATCH.match(tag)})
                if names:
                    rec = {"touch": names}
                    for key in ("attack_power", "armor", "vitality", "spell_power", "spell_power_aard", "spell_power_igni", "spell_power_yrden", "spell_power_quen", "spell_power_axii", "staminaRegen"):
                        mult = sum(v for ty, v in attr(e, key) if ty == "mult"); add = sum(v for ty, v in attr(e, key) if ty == "add")
                        if mult or add: rec[key] = {"mult": mult, "add": add}
                    r["eff"][n] = rec
        for k, blob in AR.files_of(g, "abilities", ("effects.xml",)):
            if k[0] == "xml.bundle":
                for m in re.finditer(r'<effect\s+name_name\s*=\s*"([^"]+)"[^>]*?effectNameLocalisationKey_name\s*=\s*"([^"]+)"', AR.text_of(blob)):
                    lab = strs.get(keys.get(w3dec.h(m.group(2))))
                    if lab: r["eff_names"][m.group(1)] = lab
    for k in ("syn", "surv_mult", "surv"):
        if R["ng"][k] != R["ng_plus"][k]: sys.exit("%s differs between NG and NG+: store it per ruleset" % k)
    out = {"lvl": {rs: R[rs]["lvl"] for rs in R}, "con": {rs: R[rs]["con"] for rs in R}, "syn": R["ng"]["syn"], "surv_mult": R["ng"]["surv_mult"], "surv": R["ng"]["surv"],
           "note": "from the game's ability XML (tools/make_stats.py): Lvl2.. = [vitality base, attack_power add, spell_power mult]"}
    differs = {}
    if R["ng"]["spl"] != R["ng_plus"]["spl"] or R["ng"]["sgn"] != R["ng_plus"]["sgn"]: sys.exit("spl or sgn differ between NG and NG+: store them per ruleset")
    out["spl"] = R["ng"]["spl"]; out["sgn"] = R["ng"]["sgn"]
    out["armor_type"] = dict(R["ng"]["armor_type"])
    for n, t in R["ng_plus"]["armor_type"].items():
        if out["armor_type"].setdefault(n, t) != t: sys.exit("armour type of %s differs between NG and NG+: store it per ruleset" % n)
    for k in ("touch", "eff", "eff_names", "mods"):
        out[k] = R["ng"][k]; d = {n: R["ng_plus"][k].get(n) for n in set(R["ng"][k]) | set(R["ng_plus"][k]) if R["ng"][k].get(n) != R["ng_plus"][k].get(n)}
        if d: out[k + "p"] = d; differs[k] = sorted(d)
    out["labels"] = {k: strs.get(keys.get(w3dec.h(k))) for k in LABELS}
    assert all(out["labels"].values()), [k for k, v in out["labels"].items() if not v]
    assert out["lvl"]["ng"][:2] == [[100, 4, 0.02], [100, 4, 0.02]], out["lvl"]["ng"][:2]
    (ROOT / "data" / "STATS.json").write_text(json.dumps(out, separators=(",", ":"), sort_keys=True) + "\n", encoding="utf-8")
    print("levels %s, %d skills that touch a watched stat, survival: %s; NG+ differs for: %s" % ({k: len(v) for k, v in out["lvl"].items()}, len(out["touch"]), out["surv"], differs or "nothing"))


if __name__ == "__main__":
    main()
