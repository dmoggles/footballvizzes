from dataclasses import dataclass
from footmav.data_definitions.whoscored.constants import EventType


@dataclass
class EventDefinition:
    label: str
    event_type: EventType
    outcome_type: int
    marker: str
    color: str = None
    edge_color: str = None
    size_mult: float = 1


defensive_events = [
    EventDefinition("Recovery", EventType.BallRecovery, 1, "o"),
    EventDefinition("Interception", EventType.Interception, 1, "X", size_mult=1.5),
    EventDefinition("Interception", EventType.BlockedPass, 1, "X", size_mult=1.5),
    EventDefinition(
        "Tackle Won (won ball)", EventType.Tackle, 1, "D", "green", "lightgreen"
    ),
    EventDefinition(
        "Tackle Won (other team kept ball)",
        EventType.Tackle,
        0,
        "D",
        "olive",
        "lightgreen",
    ),
    EventDefinition("Tackle Lost", EventType.Challenge, 0, "D", "red", "orangered"),
    EventDefinition(
        "Foul",
        EventType.Foul,
        0,
        "P",
        size_mult=1.5,
        color="red",
        edge_color="orangered",
    ),
    EventDefinition("Clearance", EventType.Clearance, 1, "*", size_mult=2),
    EventDefinition("Header Won", EventType.Aerial, 1, "^", "green", "lightgreen", 1.5),
    EventDefinition("Header Lost", EventType.Aerial, 0, "^", "red", "orangered", 1.5),
    EventDefinition("Block", EventType.Save, 1, "s", size_mult=1),
]
