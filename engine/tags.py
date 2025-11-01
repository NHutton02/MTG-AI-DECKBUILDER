import re
from typing import Dict, Set

# Simple keyword-based tagging for oracle_text and type_line.
KEYWORDS = {
    "ramp": ["search your library for a basic land", "add {", "mana of any color", "cultivate", "rampant growth", "treasure"],
    "removal": ["destroy target", "exile target", "deal damage to", "counter target", "fight target"],
    "draw": ["draw a card", "scry", "investigate", "learn", "connive"],
    "token": ["create a", "token"],
    "lifegain": ["you gain", "lifelink"],
    "counter_synergy": ["+1/+1 counter", "proliferate"],
    "graveyard": ["return target", "from your graveyard", "mill"],
    "artifact": ["artifact"],
    "enchantment": ["enchantment"],
    "blink": ["exile target creature you control, then return", "flicker"],
    "burn": ["damage to any target", "noncombat damage"],
    "counterspell": ["counter target spell"],
    "board_wipe": ["destroy all", "exile all"],
}

TYPE_FLAGS = {
    "creature": "Creature",
    "instant": "Instant",
    "sorcery": "Sorcery",
    "artifact": "Artifact",
    "enchantment": "Enchantment",
    "planeswalker": "Planeswalker",
    "land": "Land",
}

def make_tags(card: Dict) -> Set[str]:
    tags: Set[str] = set()
    text = (card.get("oracle_text") or "").lower()
    types = (card.get("type_line") or "").lower()
    for tag, needles in KEYWORDS.items():
        for n in needles:
            if n.lower() in text:
                tags.add(tag); break
    for key, word in TYPE_FLAGS.items():
        if word.lower() in types:
            tags.add(key)
    # quick role hints
    if "haste" in text or "menace" in text or "flying" in text:
        tags.add("threat")
    if "draw a card" in text or "connive" in text:
        tags.add("card_advantage")
    if "{r}" in (card.get("mana_cost") or "").lower():
        tags.add("red_pip")
    if "{g}" in (card.get("mana_cost") or "").lower():
        tags.add("green_pip")
    if "{u}" in (card.get("mana_cost") or "").lower():
        tags.add("blue_pip")
    if "{w}" in (card.get("mana_cost") or "").lower():
        tags.add("white_pip")
    if "{b}" in (card.get("mana_cost") or "").lower():
        tags.add("black_pip")
    return tags
