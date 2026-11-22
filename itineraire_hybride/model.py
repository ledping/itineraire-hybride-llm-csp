"""Représentation formelle des activités, itinéraires et événements perturbateurs."""
from dataclasses import dataclass, field


@dataclass
class Activity:
    id: str
    name: str
    place: tuple[float, float]  # coordonnées en km dans un repère local
    duration: int  # minutes
    opens: int  # minutes depuis minuit
    closes: int
    outdoor: bool = False
    preference: int = 5  # 1 à 10, poids de la préférence du touriste
    mandatory: bool = False


@dataclass
class Visit:
    activity_id: str
    start: int

    def end(self, activities: dict[str, Activity]) -> int:
        return self.start + activities[self.activity_id].duration


@dataclass
class Itinerary:
    visits: list[Visit]

    def order(self) -> list[str]:
        return [v.activity_id for v in sorted(self.visits, key=lambda v: v.start)]

    def starts(self) -> dict[str, int]:
        return {v.activity_id: v.start for v in self.visits}


@dataclass
class Event:
    """Perturbation extérieure. kind : rain, closure, strike."""
    kind: str
    start: int = 0
    end: int = 24 * 60
    activity_id: str | None = None  # pour une fermeture
    travel_factor: float = 1.0  # pour une grève des transports
    description: str = ""


@dataclass
class Problem:
    activities: list[Activity]
    day_start: int
    day_end: int
    speed_kmh: float = 20.0
    events: list[Event] = field(default_factory=list)

    def by_id(self) -> dict[str, Activity]:
        return {a.id: a for a in self.activities}

    def travel_minutes(self, a: Activity, b: Activity) -> int:
        factor = 1.0
        for e in self.events:
            if e.kind == "strike":
                factor = max(factor, e.travel_factor)
        distance = abs(a.place[0] - b.place[0]) + abs(a.place[1] - b.place[1])
        return round(distance / self.speed_kmh * 60 * factor)
