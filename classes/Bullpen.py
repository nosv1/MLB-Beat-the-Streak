from classes.Pitcher import Pitcher

class Bullpen:
    def __init__(self) -> None:
        self.pitchers: list[Pitcher] = []
        
        # per bf is average of the whole bullpen, but weighted based on batters faced over the whole bullpen
        # so like if a pitcher has a .5 h_per_bf but 10 bf out of the bullpens 30, then it'd be .5 * (10 / 30)
        self.h_per_bf: float = None
        self.h_per_bf_normalized: float = None

        self.k_per_bf: float = None
        self.k_per_bf_normalized: float = None

    def set_stats(self) -> None:

        sum_bf: int = sum(pitcher.bf for pitcher in self.pitchers)
        per_bf: dict[str, list[float]] = {"h": [], "k": []}
        for pitcher in self.pitchers:
            per_bf["h"].append(pitcher.h_per_bf * (pitcher.bf / sum_bf))
            per_bf["k"].append(pitcher.k_per_bf * (pitcher.bf / sum_bf))

        self.h_per_bf = sum(per_bf["h"])
        self.k_per_bf = sum(per_bf["k"])