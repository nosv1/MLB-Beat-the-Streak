class Odds:
    def __init__(self) -> None:
        self.moneyline: int = None
        self.implied: float = None
        self.implied_normalized: float = None
        
        self.total: float = None
        self.total_normalized: float = None

    def set_implied_odds(self) -> float:
        if self.moneyline < 0:
            self.implied = (-1 * self.moneyline) / (-1 * self.moneyline + 100)
        else: 
            self.implied = 100 / (self.moneyline + 100)