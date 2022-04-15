class Odds:
    def __init__(self, moneyline: int = None, total: float = None) -> None:
        self.moneyline: int = moneyline
        self.implied: float = self.get_implied_odds() if self.moneyline else None
        self.implied_normalized: float = None
        
        self.total: float = total
        self.total_normalized: float = None

    def get_implied_odds(self) -> float:
        if self.moneyline < 0:
            return (-1 * self.moneyline) / (-1 * self.moneyline + 100)
        else: 
            return 100 / (self.moneyline + 100)