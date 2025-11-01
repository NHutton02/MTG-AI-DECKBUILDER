#!/usr/bin/env python3
import argparse
from engine.builder import build_deck

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--format", default="standard", choices=["standard","commander"])
    p.add_argument("--seed", required=True)
    p.add_argument("--export", choices=["arena","mtgo","csv"])
    args = p.parse_args()

    deck = build_deck(args.seed, args.format)
    print("=== Decklist (mainboard) ===")
    for line in deck.get("mainboard", []):
        print(line)
    print("\n=== Explanation ===")
    print(deck.get("explanation",""))

if __name__ == "__main__":
    main()
