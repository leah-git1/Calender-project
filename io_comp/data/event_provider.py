import csv
import os
from typing import List, Protocol
from datetime import datetime, time
from io_comp.models.domain import Event, TimeSlot

class EventProviderError(Exception):
    """
    CUSTOM EXCEPTION:
    Raised when the application fails to load calendar data.
    Prevents 'Silent Failures' where missing data is mistaken for an empty calendar.
    """
    pass


class EventProvider(Protocol):
    """Protocol (Interface) for fetching events."""
    def get_events(self) -> List[Event]:
        ...


class CsvEventProvider:
    """Concrete implementation that reads events from a CSV file."""
    def __init__(self, file_path: str):
        self.file_path = file_path

    def get_events(self) -> List[Event]:
        events = []
        
        # FAIL-FAST: If the file is missing, halt the system immediately!
        # Returning an empty list here would cause catastrophic "Double Bookings"
        if not os.path.exists(self.file_path):
            raise EventProviderError(f"CRITICAL: Calendar file not found at {self.file_path}")

        with open(self.file_path, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if not row or len(row) < 4:
                    continue
                
                name = row[0].strip()
                subject = row[1].strip()
                start_time_str = row[2].strip()
                end_time_str = row[3].strip()

                start_time = datetime.strptime(start_time_str, "%H:%M").time()
                end_time = datetime.strptime(end_time_str, "%H:%M").time()

                events.append(Event(name, subject, TimeSlot(start_time, end_time)))
                
        return events