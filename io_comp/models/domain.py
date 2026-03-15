from dataclasses import dataclass
from datetime import time

@dataclass(frozen=True)
class CalendarConfig:
    """
    Configuration class to hold hardcoded values.
    Solves the 'Hardcoded working hours' problem.
    """
    day_start: time = time(7, 0)
    day_end: time = time(19, 0)

@dataclass(frozen=True)
class TimeSlot:
    """
    Immutable Model using frozen=True.
    Prevents shared state bugs and accidental mutations.
    """
    start_time: time
    end_time: time

@dataclass(frozen=True)
class Event:
    """Immutable Event Model."""
    person_name: str
    subject: str
    time_slot: TimeSlot