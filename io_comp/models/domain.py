from dataclasses import dataclass
from datetime import time

@dataclass
class TimeSlot:
    """
    Represents a specific time interval within a single day.
    """
    start_time: time
    end_time: time

@dataclass
class Event:
    """
    Represents a calendar event for a specific person.
    """
    person_name: str
    subject: str
    time_slot: TimeSlot