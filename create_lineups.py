from datetime import datetime
import enum
import json
import os
import pickle

from dk_classes import DK_Batters_Scoring, Odds, Prop, Batter, Event

def get_best_batter_in_tier(tier_batters: list[Batter], dk_batters: list[Batter]) -> Batter:
    for batter in dk_batters:
        for tier_batter in tier_batters:
            if batter.name == tier_batter.name:
                tier_batter.total_points = batter.total_points 
                return tier_batter

def main():

    with open(f"./draft_kings/MLB_ALL_HITTERS_Projections_4_25_2022.csv", 'r') as f:
        dk_batters: list[Batter] = [l.split(',') for l in f.readlines()][1:]
        for i, batter in enumerate(dk_batters):
            dk_batters[i] = Batter(
                name=batter[0],
            )
            dk_batters[i].total_points = float(batter[6])

    dk_batters.sort(key=lambda x: x.total_points, reverse=True)

    # dk_batters: list[Batter] = pickle.load(open('./pickles/dk_batters.pkl', 'rb')).values()
    exclude: list[str] = [""]

    for file in os.listdir('./draft_kings/DKSalaries'):
        with open(f'./draft_kings/DKSalaries/{file}', 'r') as f:
            slate = [l.strip().split(',') for l in f.readlines()]
            lineup: list[list[Batter]] = [slate[0], []]

            for i, batter in enumerate(slate):

                # found line above header
                if len(batter) == 1:
                    break

            current_tier = None
            tier_batters: list[Batter] = []
            for j, batter in enumerate(slate[i+2:] + ['']):
                tier = batter[11] if len(batter) > 11 else None

                if not current_tier or tier == current_tier:
                    current_tier = tier

                    tier_batter = Batter(name=batter[9])
                    tier_batter.id = batter[10]
                    if tier_batter.name not in exclude:
                        tier_batters.append(tier_batter)

                else:
                    current_tier = tier
                    batter: Batter = get_best_batter_in_tier(tier_batters, dk_batters)
                    print(f" {batter.total_points:.2f} - {batter.name}")
                    lineup[1].append(batter)
                    tier_batters: list[Batter] = []

            print(f"{sum([b.total_points for b in lineup[1]]):.2f} - Total\n")

            with open(f'draft_kings/lineup_{file}', 'w') as f:
                f.write(
                    '\n'.join(
                        ','.join(
                            [b.id if isinstance(b, Batter) else b for b in l]
                        ) for l in lineup
                    )
                )
    return

if __name__ == "__main__":
    main()