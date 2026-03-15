from typing import List, Tuple
from datetime import time, timedelta

# Import our immutable models and the new configuration class
from io_comp.models.domain import TimeSlot, CalendarConfig
from io_comp.data.event_provider import EventProvider

class CalendarService:
    """
    Service responsible for core calendar business logic.
    Fully adheres to SOLID principles, Dependency Injection, and Immutability.
    """
    def __init__(self, event_provider: EventProvider, config: CalendarConfig = CalendarConfig()):
        """
        Dependency Injection applied:
        Injecting both the Repository (EventProvider) and the Configuration (CalendarConfig).
        This makes the class highly testable and configurable.
        """
        self._event_provider = event_provider
        self._config = config

    def find_shared_available_slots(self, person_list: List[str], duration: timedelta) -> List[TimeSlot]:
        """
        Finds the ranges of *possible start times* for the requested duration.
        Returns a List[TimeSlot] to accurately model the domain and fulfill 
        the expected output format (e.g., "09:40 - 12:00").
        """
        required_minutes = int(duration.total_seconds() // 60)
        
        # Get all free gaps in the calendar
        all_gaps = self._get_all_gaps(person_list)
        
        available_start_ranges = []
        for gap_start, gap_end in all_gaps:
            gap_duration = self._minutes_between(gap_start, gap_end)
            
            if gap_duration >= required_minutes:
                earliest_start = gap_start
                
                # Calculate the absolute latest time a meeting can start within this gap
                gap_end_minutes = gap_end.hour * 60 + gap_end.minute
                latest_start_minutes = gap_end_minutes - required_minutes
                latest_start = time(latest_start_minutes // 60, latest_start_minutes % 60)
                
                available_start_ranges.append(TimeSlot(earliest_start, latest_start))

        return available_start_ranges

    def find_max_available_slot(self, person_list: List[str]) -> Tuple[time, time, int]:
        """BONUS FEATURE: Finds the single longest available time slot for fallback suggestions."""
        all_gaps = self._get_all_gaps(person_list)
        if not all_gaps:
            return None, None, 0
            
        max_gap_duration = 0
        best_gap_start, best_gap_end = None, None
        
        for gap_start, gap_end in all_gaps:
            current_duration = self._minutes_between(gap_start, gap_end)
            if current_duration > max_gap_duration:
                max_gap_duration = current_duration
                best_gap_start = gap_start
                best_gap_end = gap_end
                
        return best_gap_start, best_gap_end, max_gap_duration

    def find_busiest_person(self, person_list: List[str]) -> tuple[str, int]:
        """BONUS FEATURE: Identifies the bottleneck (person with most meeting minutes)."""
        busy_minutes = {person: 0 for person in person_list}
        all_events = self._event_provider.get_events()
        
        for event in all_events:
            if event.person_name in busy_minutes:
                duration = self._minutes_between(event.time_slot.start_time, event.time_slot.end_time)
                busy_minutes[event.person_name] += duration
                
        busiest_person = max(busy_minutes.items(), key=lambda item: item[1])
        return busiest_person

    def _get_all_gaps(self, person_list: List[str]) -> List[Tuple[time, time]]:
        """
        Core Algorithm: Merge Overlapping Intervals (O(N log N)).
        Safely handles immutable (frozen=True) DataClasses.
        """
        all_events = self._event_provider.get_events()
        target_persons = set(person_list)
        
        relevant_slots = [
            event.time_slot for event in all_events 
            if event.person_name in target_persons
        ]

        # If no events exist, the entire day (based on config) is free
        if not relevant_slots:
            return [(self._config.day_start, self._config.day_end)]

        # Step 1: Sort by start time
        relevant_slots.sort(key=lambda slot: slot.start_time)
        
        # Step 2: Merge overlapping intervals
        merged_slots = [TimeSlot(relevant_slots[0].start_time, relevant_slots[0].end_time)]
        
        for current in relevant_slots[1:]:
            last_merged = merged_slots[-1]
            if current.start_time <= last_merged.end_time:
                # IMMUTABILITY FIX: We create a NEW TimeSlot instead of mutating the existing one
                new_end_time = max(last_merged.end_time, current.end_time)
                merged_slots[-1] = TimeSlot(last_merged.start_time, new_end_time)
            else:
                merged_slots.append(TimeSlot(current.start_time, current.end_time))

        # Step 3: Extract the free gaps between the busy blocks
        gaps = []
        if self._minutes_between(self._config.day_start, merged_slots[0].start_time) > 0:
            gaps.append((self._config.day_start, merged_slots[0].start_time))

        for i in range(len(merged_slots) - 1):
            gap_start = merged_slots[i].end_time
            gap_end = merged_slots[i+1].start_time
            if self._minutes_between(gap_start, gap_end) > 0:
                gaps.append((gap_start, gap_end))

        if self._minutes_between(merged_slots[-1].end_time, self._config.day_end) > 0:
            gaps.append((merged_slots[-1].end_time, self._config.day_end))

        return gaps

    def _minutes_between(self, start: time, end: time) -> int:
        """Helper to safely calculate minutes between two time objects."""
        if start >= end:
            return 0
        return (end.hour * 60 + end.minute) - (start.hour * 60 + start.minute)