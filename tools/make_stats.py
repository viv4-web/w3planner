#!/usr/bin/env python3
"""The numbers behind the Player Stats screen (v32): data/STATS.json, from the game's ability XML (gameplay/abilities and gameplay/abilities_plus in xml.bundle).

    python tools/make_stats.py --bundle ~/incoming/gamedata/bundles/xml.bundle

lvl      per level 2..: [vitality base, attack_power add, spell_power mult] from the abilities Lvl2..LvlN (geralt_stats.xml), one table per ruleset (abilities = ng, abilities_plus = ng_plus)
con      the base character ability ConGeralt (geralt_stats.xml): vitality, stamina, toxicity, critical hit chance and damage, poison and bleeding resistance
surv     the skills that add 1% Vitality per level while equipped (PlayerAbilityManager.ws 162-186: perk path, isReworked or isUnchangedLegacy); `survival_vitality` has vitality mult 0.01
touch    skill id -> the watched attributes its ability changes (a skill that changes a stat the screen does not model makes that stat show "—")
syn      the Synergy step (perk_43 synergy_bonus, 0.1 per level)
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
attribute_name_staminaregen_out_of_combat attribute_name_staminaregen bonus_herb_chance instant_kill_chance human_exp_bonus_when_fatal nonhuman_exp_bonus_when_fatal""".split()


def text(path):
    return re.sub(r"<!--.*?-->", "", Path(path).read_text(encoding="utf-8-sig"), flags=re.S)


class Ab:
    """One <ability> block read with regular expressions (the game's XML repeats attributes on some tags, so no XML parser): children = [(tag, {attr: value})]"""
    def __init__(self, body):
        self.children = [(m.group(1), dict(re.findall(r'([\w]+)\s*=\s*"([^"]*)"', m.group(2)))) for m in re.finditer(r"<([A-Za-z_][\w]*)\s+([^>]*?)/?>", body)]


def abilities(t):
    return {m.group(1): Ab(m.group(2)) for m in re.finditer(r'<ability\s+name\s*=\s*"([^"]+)"[^>]*>(.*?)</ability>', t, re.S)}


def attr(a, name):
    """[(type, min)] of an attribute element"""
    return [(c.get("type") or "base", float(c["min"])) for tag, c in a.children if tag == name and "min" in c]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); ap.add_argument("--bundle", required=True); ap.add_argument("--game-dir", default=str(Path.home() / "incoming" / "gamedata")); a = ap.parse_args()
    tmp = tempfile.mkdtemp(prefix="w3stats-")
    subprocess.run([sys.executable, str(ROOT / "tools/extract/bundle.py"), "extract", a.bundle, "--glob", "gameplay\\abilities*\\geralt_*.xml", "--out", tmp], check=True, capture_output=True)
    out = {"lvl": {}, "con": {}, "surv": [], "touch": {}, "syn": None, "note": "from the game's ability XML (tools/make_stats.py): Lvl2.. = [vitality base, attack_power add, spell_power mult]"}
    for rs, d in (("ng", "abilities"), ("ng_plus", "abilities_plus")):
        st = abilities(text(Path(tmp) / "gameplay" / d / "geralt_stats.xml")); rows = []
        for n in range(2, 101):
            ab = st.get("Lvl%d" % n)
            if ab is None: break
            g = lambda k, t: sum(v for ty, v in attr(ab, k) if ty == t)
            rows.append([g("vitality", "base"), g("attack_power", "add"), round(g("spell_power", "mult"), 6)])
        out["lvl"][rs] = rows
        con = st["ConGeralt"]; c = lambda k, t="base": next((v for ty, v in attr(con, k) if ty == t), 0)
        out["con"][rs] = {"vitality": c("vitality"), "stamina": c("stamina"), "toxicity": c("toxicity"), "crit_chance": c("critical_hit_chance"), "crit_damage": c("critical_hit_damage_bonus", "add"),
                          "poison_resist": c("poison_resistance_perc"), "bleeding_resist": c("bleeding_resistance_perc"),
                          "vit_regen": c("vitalityRegen", "add"), "vit_combat_regen": c("vitalityCombatRegen", "add"), "stamina_ooc_mult": c("staminaOutOfCombatRegen", "mult")}
        sk = text(Path(tmp) / "gameplay" / d / "geralt_skills.xml"); ab = abilities(sk)
        if rs == "ng":
            out["syn"] = attr(ab["perk_43"], "synergy_bonus")[0][1]
            out["surv_mult"] = attr(ab["survival_vitality"], "vitality")[0][1]
            for m in re.finditer(r"<skill\s([^>]*)>", sk):
                at = dict(re.findall(r'(\w+)\s*=\s*"([^"]*)"', m.group(1))); n = at.get("skill_name")
                if n and n.startswith("perk_") and (at.get("isReworked") == "1" or at.get("isUnchangedLegacy") == "1"): out["surv"].append(n)
        for n, e in ab.items():
            names = sorted({tag for tag, _ in e.children if tag != "tags" and WATCH.match(tag)})
            if names and (re.match(r"^(sword|magic|alchemy|perk)_", n) or n.startswith("mutation")): out["touch"].setdefault(n, [])[:] = sorted(set(out["touch"].get(n, [])) | set(names))
    sys.path.insert(0, str(ROOT / "tools" / "extract")); import w3dec
    strs, keys = w3dec.decode(str(Path(a.game_dir) / "en.w3strings")); out["labels"] = {k: strs.get(keys.get(w3dec.h(k))) for k in LABELS}
    # active effects (the player's effect manager in a save: W3Effect_* with an abilityName): what each ability changes, and the labels the game shows for them
    out["eff"] = {}; out["eff_names"] = {}
    for f in ("effects.xml", "effects_potions.xml", "effects_mutagens.xml", "misc.xml", "weather_abl.xml"):
        pth = Path(tmp) / "gameplay" / "abilities" / f
        if not pth.is_file():
            subprocess.run([sys.executable, str(ROOT / "tools/extract/bundle.py"), "extract", a.bundle, "--glob", "gameplay\\abilities\\" + f, "--out", tmp], check=True, capture_output=True)
        t = text(pth)
        for n, e in abilities(t).items():
            names = sorted({tag for tag, _ in e.children if tag != "tags" and WATCH.match(tag)})
            if names:
                rec = {"touch": names}
                for key in ("attack_power", "armor", "vitality"):
                    mult = sum(v for ty, v in attr(e, key) if ty == "mult"); add = sum(v for ty, v in attr(e, key) if ty == "add")
                    if mult or add: rec[key] = {"mult": mult, "add": add}
                out["eff"][n] = rec
        if f == "effects.xml":
            for m in re.finditer(r'<effect\s+name_name\s*=\s*"([^"]+)"[^>]*?effectNameLocalisationKey_name\s*=\s*"([^"]+)"', t):
                lab = strs.get(keys.get(w3dec.h(m.group(2))))
                if lab: out["eff_names"][m.group(1)] = lab
    assert all(out["labels"].values()), [k for k, v in out["labels"].items() if not v]
    assert out["lvl"]["ng"][:2] == [[100, 4, 0.02], [100, 4, 0.02]], out["lvl"]["ng"][:2]
    (ROOT / "data" / "STATS.json").write_text(json.dumps(out, separators=(",", ":"), sort_keys=True) + "\n", encoding="utf-8")
    print("levels %s, %d skills that touch a watched stat, survival: %s" % ({k: len(v) for k, v in out["lvl"].items()}, len(out["touch"]), out["surv"]))


if __name__ == "__main__":
    main()
