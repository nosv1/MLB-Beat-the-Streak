from datetime import datetime
import enum
import json
import os
import pickle

from dk_classes import DK_Batters_Scoring, Odds, Prop, Batter, Event

def get_best_batter_in_tier(tier_batters: list[Batter], dk_batters: list[Batter]) -> Batter:
    for name in dk_batters:
        for tier_batter in tier_batters:
            if name == tier_batter.name:
                return tier_batter

def main():
    # loop DKSalaries folder and load the csv files

    dk_batters: list[Batter] = pickle.load(open("dk_batters.pkl", "rb"))
    lineups: list[int] = []

    for file in os.listdir('./DKSalaries'):
        with open(f'./DKSalaries/{file}', 'r') as f:
            slate = [l.strip().split(',') for l in f.readlines()]
            lineups += [slate[0]]

            for i, batter in enumerate(slate):

                # found line above header
                if len(batter) == 1:
                    break

            current_tier = None
            tier_batters = []
            lineup: list[int] = []
            for j, batter in enumerate(slate[i+2:] + ['']):
                tier = batter[11] if len(batter) > 11 else None

                if not current_tier or tier == current_tier:
                    current_tier = tier

                    tier_batters.append(
                        Batter(name=batter[9])
                    )
                    tier_batters[-1].id = batter[10]

                else:
                    current_tier = tier
                    batter = get_best_batter_in_tier(tier_batters, dk_batters)
                    print(f"{batter.name}")
                    lineup.append(batter.id)
                    tier_batters = []

            lineups.append(lineup)

        print()

        with open(f'lineup_{int(datetime.now().timestamp())}.csv', 'w') as f:
            f.write('\n'.join(','.join(l) for l in lineups))
    return

if __name__ == "__main__":
    main()