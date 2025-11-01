#!/usr/bin/env python3
import json, os
from pathlib import Path
import requests

RAW_PATH = Path("data/cards/scryfall_raw.json")
CLEAN_PATH = Path("data/cards/cards_clean.json")
BULK_ENDPOINT = "https://api.scryfall.com/bulk-data/default-cards"

KEEP_FIELDS = {
    "id","name","mana_cost","type_line","oracle_text","colors","color_identity",
    "cmc","set","set_name","rarity","keywords","legalities","image_uris","prices"
}

def download_bulk() -> list:
    info = requests.get(BULK_ENDPOINT, timeout=60).json()
    url = info["download_uri"]
    print(f"[info] downloading bulk JSON from {url}")
    data = requests.get(url, timeout=300).json()
    return data

def clean(cards: list) -> list:
    cleaned = []
    for c in cards:
        if c.get("layout") in {"art_series","token","double_faced_token","emblem"}:
            continue
        d = {k: c.get(k) for k in KEEP_FIELDS}
        d["oracle_text"] = (d.get("oracle_text") or "").strip()
        if isinstance(d.get("image_uris"), dict):
            d["image_small"] = d["image_uris"].get("small")
            d["image_normal"] = d["image_uris"].get("normal")
        d.pop("image_uris", None)
        cleaned.append(d)
    return cleaned

def main():
    os.makedirs("data/cards", exist_ok=True)
    all_cards = download_bulk()
    with open(RAW_PATH, "w", encoding="utf-8") as f:
        json.dump(all_cards, f, ensure_ascii=False)
    print(f"[ok] wrote {RAW_PATH} with {len(all_cards)} cards")

    cleaned = clean(all_cards)
    with open(CLEAN_PATH, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False)
    print(f"[ok] wrote {CLEAN_PATH} with {len(cleaned)} cards")

if __name__ == "__main__":
    main()
