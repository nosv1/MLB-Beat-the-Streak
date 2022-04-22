from datetime import datetime
from pytz import timezone

class DK_Batters_Scoring:
    points: dict = {
        "Hits": 0,  # not included in scoring, just need to sort by hits for BTS

        "Singles": 3,
        "Doubles": 5,
        "Triples": 8,
        "Home Runs": 10,
        "RBIs": 2,
        "Runs Scored": 2,
        # "Walks": 2,  # no props for
        # "Hit By Pitch": 2,  # no props for
        "Total Bases": 2,  # used for walks / hit by pitch
        "Stolen Bases": 5
    }
    points["Home Runs"] = points["Home Runs"] + points["RBIs"] + points["Runs Scored"]

class Odds:
    def __init__(self, label: str, odds: int = None, line: float = None) -> None:
        self.label: str = label  # over/under
        self.odds: int = odds  # -145, +105, etc
        self.line: float = line  # 0.5, 1.5, etc

        if self.odds and self.line:
            self.implied_odds: float = self.get_implied_odds(odds)
            self.implied_outcome: float = self.get_implied_outcome(self.line, self.implied_odds)

    def get_implied_outcome(self, line: float, implied_odds: float) -> float:
        if self.label == "Over":
            return implied_odds * line
        else:
            return implied_odds * (line / 2)

    def get_implied_odds(self, odds: int) -> float:
        if odds < 0:
            return (-1 * odds) / (-1 * odds + 100)
        else: 
            return 100 / (odds + 100)

class Prop:
    def __init__(self, name: str) -> None:
        self.name = name
        self.odds: list[Odds] = []
        self.points: float = None

    def get_average_odds(self) -> Odds:
        odds = Odds(
            label="Average"
        )
        odds.implied_outcome = sum([x.implied_outcome for x in self.odds]) / len(self.odds)
        return odds

    def calculate_points(self) -> None:
        self.points = self.odds[-1].implied_outcome * DK_Batters_Scoring.points[self.name]

class Batter:
    def __init__(self, name: str) -> None:
        self.name: str = name
        self.props: dict[str, Prop] = {}
        self.total_points: float = None

class Event:
    def __init__(self, id: str, name: str, start_date: datetime) -> None:
        self.id: str = id
        self.name: str = name
        self.start_date: datetime = timezone("UTC").localize(start_date).astimezone(timezone("America/Chicago"))

    def to_string(self) -> str:
        return f"{datetime.strftime(self.start_date, '%m-%d %I:%M %p')} - {self.name}"