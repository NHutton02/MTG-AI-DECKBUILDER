import json, math, re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, Counter

from .legality import is_legal_standard, is_legal_commander
from .mana import hypergeom_successes
from . import tags as tagger

CARDS_PATH = Path("data/cards/cards_clean.json")

BASIC_LANDS = {
    "W": "Plains",
    "U": "Island",
    "B": "Swamp",
    "R": "Mountain",
    "G": "Forest",
}
def count_pips(mana_cost: str | None, color: str) -> int:
    """Count occurrences of a color pip (e.g., {R}) in the mana_cost string."""
    if not mana_cost:
        return 0
    mc = mana_cost.upper()
    return mc.count(f"{{{color}}}")

def load_cards() -> List[Dict]:
    with open(CARDS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def find_seed_card(seed: str, cards: List[Dict]) -> Optional[Dict]:
    seed_lower = seed.lower()
    exact = [c for c in cards if (c.get("name") or "").lower() == seed_lower]
    if exact:
        return exact[0]
    # fallback: substring match
    subs = [c for c in cards if seed_lower in (c.get("name") or "").lower()]
    return subs[0] if subs else None

def card_is_legal_in_format(card: Dict, fmt: str) -> bool:
    leg = (card.get("legalities") or {})
    state = leg.get(fmt, "not_legal")
    return state in {"legal","restricted"}  # restricted rare; we still allow selection

def card_is_land(card: Dict) -> bool:
    return "Land" in (card.get("type_line") or "")

def card_colors(card: Dict) -> List[str]:
    return card.get("color_identity") or card.get("colors") or []

def derive_colors_from_seed(seed_card: Optional[Dict], seed_text: str) -> List[str]:
    if seed_card:
        cols = card_colors(seed_card)
        if cols:
            return cols
    # heuristics from text
    text = seed_text.lower()
    if any(k in text for k in ["boros","rw","red white"]):
        return ["R","W"]
    if any(k in text for k in ["izzet","ur","blue red"]):
        return ["U","R"]
    if any(k in text for k in ["golgari","bg","black green"]):
        return ["B","G"]
    if any(k in text for k in ["mono-red","red deck","rdw"]):
        return ["R"]
    return ["R"]  # default

def score_card_for_strategy(card: Dict, colors: List[str], seed_card: Optional[Dict], strategy_text: str) -> float:
    score = 0.0
    # color fit
    cids = set(card_colors(card))
    if not colors:
        color_fit = 0.5
    else:
        color_fit = len(cids & set(colors)) / max(1, len(cids | set(colors)))
    score += 2.0 * color_fit

    # role tags
    t = tagger.make_tags(card)
    if "removal" in t: score += 0.8
    if "draw" in t or "card_advantage" in t: score += 0.7
    if "ramp" in t: score += 0.7
    if "creature" in t and card.get("cmc", 0) <= 2: score += 0.5  # cheap curve
    if "threat" in t and card.get("cmc", 0) <= 3: score += 0.4

    # strategy keywords
    s = strategy_text.lower()
    ot = (card.get("oracle_text") or "").lower() + " " + (card.get("type_line") or "").lower()
    if any(k in s for k in ["aggro","burn","haste","prowess","swiftspear"]):
        if "instant" in ot or "sorcery" in ot: score += 0.4  # spells matter
        if "haste" in ot: score += 0.5
        if "damage to any target" in ot: score += 0.6
    if any(k in s for k in ["+1/+1","counters","proliferate"]):
        if "+1/+1 counter" in ot or "proliferate" in ot: score += 0.8
    if any(k in s for k in ["lifegain","soul warden","angel"]):
        if "you gain" in ot or "lifelink" in ot: score += 0.7
        if "angel" in ot: score += 0.5

    # keep lands low score (we'll add separately)
    if card_is_land(card): score -= 2.0
    return score

def choose_lands(count_needed: int, pip_counts: Counter, format_colors: List[str]) -> List[str]:
    if not format_colors:
        format_colors = ["R"]
    # Estimate proportions from pip counts
    total_pips = sum(pip_counts[c] for c in format_colors) or len(format_colors)
    lands = []
    for c in format_colors:
        share = (pip_counts[c] / total_pips) if total_pips else (1/len(format_colors))
        lands += [BASIC_LANDS[c]] * int(round(share * count_needed))
    # adjust to exact count
    while len(lands) < count_needed: lands.append(BASIC_LANDS[format_colors[0]])
    while len(lands) > count_needed: lands.pop()
    return lands

def build_standard(seed: str, cards: List[Dict]) -> Dict:
    seed_card = find_seed_card(seed, cards)
    colors = derive_colors_from_seed(seed_card, seed)
    # candidate nonlands legal in Standard and within colors
    cands = []
    for c in cards:
        if not card_is_legal_in_format(c, "standard"): continue
        if card_is_land(c): continue
        if colors and (set(card_colors(c)) - set(colors)): continue
        cands.append(c)

    # score
    scored = [(score_card_for_strategy(c, colors, seed_card, seed), c) for c in cands]
    scored.sort(reverse=True, key=lambda x: x[0])

    deck: List[str] = []
    counts = Counter()
    pip_counts = Counter({k:0 for k in ["W","U","B","R","G"]})

    # include up to 4x seed if found and nonland
    if seed_card and not card_is_land(seed_card) and card_is_legal_in_format(seed_card, "standard"):
        copies = 4
        for _ in range(copies):
            deck.append(seed_card["name"]); counts[seed_card["name"]] += 1
        for p in card_colors(seed_card):
            pip_counts[p] += count_pips(seed_card.get("mana_cost"), p)

    # fill until 36 nonlands (we'll add ~24 lands later)
    for score, c in scored:
        name = c["name"]
        if counts[name] >= 4: continue
        if name == (seed_card["name"] if seed_card else "") and counts[name] >= 4: continue
        if "Land" in (c.get("type_line") or ""): continue
        deck.append(name); counts[name] += 1
        # tally pips
        for p in card_colors(c):
            pip_counts[p] += count_pips(c.get("mana_cost"), p)
        if len(deck) >= 36:
            break

    # lands: naive 24; adjust by average cmc
    nonland_cards = [c for _, c in scored if c["name"] in counts]
    avg_cmc = sum((c.get("cmc") or 0) for _, c in scored if c["name"] in counts) / max(1, len(counts))
    land_target = 24 if avg_cmc <= 3 else 25
    lands = choose_lands(land_target, pip_counts, colors)
    full = deck + lands

    # ensure legality size
    while len(full) < 60: full.append(lands[0])
    if not is_legal_standard(full):
        # fallback: trim extras
        full = full[:60]

    explanation = (
        f"Standard deck seeded by '{seed}'. Colors: {''.join(colors) or 'R'}.\n"

        f"Approx curve target with {land_target} lands. "
        "Non-land picks prioritize color fit, removal/draw/ramp tags, and low-CMC threats for tempo."
    )
    return {"mainboard": full, "explanation": explanation}

def build_commander(seed: str, cards: List[Dict]) -> Dict:
    seed_card = find_seed_card(seed, cards)
    if not seed_card:
        return {"mainboard": [], "explanation": "Seed card not found for Commander."}
    colors = derive_colors_from_seed(seed_card, seed)

    # singleton pool in color identity
    pool = []
    for c in cards:
        if not card_is_legal_in_format(c, "commander"): continue
        if card_is_land(c): continue
        if colors and (set(card_colors(c)) - set(colors)): continue
        pool.append(c)

    scored = [(score_card_for_strategy(c, colors, seed_card, seed), c) for c in pool]
    scored.sort(reverse=True, key=lambda x: x[0])

    deck_names: List[str] = []
    counts = Counter()
    pip_counts = Counter({k:0 for k in ["W","U","B","R","G"]})

    # commander
    deck_names.append(seed_card["name"]); counts[seed_card["name"]] += 1
    for p in card_colors(seed_card):
        pip_counts[p] += count_pips(seed_card.get("mana_cost"), p)

    # pick 62 more nonlands (commander: usually ~37 lands)
    for score, c in scored:
        nm = c["name"]
        if counts[nm] >= 1: continue
        deck_names.append(nm); counts[nm] += 1
        for p in card_colors(c):
            pip_counts[p] += count_pips(c.get("mana_cost"), p) 
        if len(deck_names) >= 63:
            break

    lands = choose_lands(37, pip_counts, colors)
    full = deck_names + lands

    # legality check
    if not is_legal_commander(full):
        # pad/trim to 100 singleton (basic lands can duplicate)
        seen = set()
        singles = []
        for n in deck_names:
            if n not in seen:
                singles.append(n); seen.add(n)
        full = singles + lands
        while len(full) < 100: full.append(lands[0])
        full = full[:100]

    explanation = (
        f"Commander deck around '{seed_card['name']}' with colors {''.join(colors)}. "
        "Singleton non-lands favor synergy tags (removal/draw/ramp) and matching color identity. "
        "Lands apportioned by colored pip demand."
    )
    return {"mainboard": full, "explanation": explanation}

def build_deck(seed: str, fmt: str = "standard") -> Dict:
    cards = load_cards()
    if fmt == "commander":
        return build_commander(seed, cards)
    return build_standard(seed, cards)
