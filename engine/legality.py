from collections import Counter

def is_legal_standard(decklist: list[str]) -> bool:
    # Basic checks: size >= 60, <= 4 copies for non-basics (we don't distinguish basics here)
    if len(decklist) < 60:
        return False
    counts = Counter(decklist)
    for name, cnt in counts.items():
        # Allow more than 4 for basic lands only
        if name.lower() in {"plains","island","swamp","mountain","forest"}:
            continue
        if cnt > 4:
            return False
    return True

def is_legal_commander(decklist: list[str]) -> bool:
    # 100 singleton (not enforcing color identity here; handled upstream)
    if len(decklist) != 100:
        return False
    counts = Counter(decklist)
    return all(c == 1 for c in counts.values())
