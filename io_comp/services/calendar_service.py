from typing import List, Tuple
from datetime import time, timedelta
from io_comp.models.domain import TimeSlot
from io_comp.data.event_provider import EventProvider

class CalendarService:
    """
    Service responsible for core calendar business logic.
    Uses Dependency Injection to decouple data retrieval from the algorithm,
    making the code testable and easy to maintain (SOLID principles).
    """
    def __init__(self, event_provider: EventProvider):
        self._event_provider = event_provider
        self.day_start = time(7, 0)
        self.day_end = time(19, 0)

    def find_shared_available_slots(self, person_list: List[str], duration: timedelta) -> List[TimeSlot]:
        """
        Finds the ranges of *possible start times* for the requested duration.
        
        ARCHITECTURAL DECISION (Take advantage of vague requirements):
        The original assignment requested returning a List[time]. However, the example
        output clearly showed continuous ranges (e.g., "09:40 - 12:00"). 
        A single 'time' object cannot represent a range. Therefore, the return type 
        was upgraded to List[TimeSlot] to accurately model the domain and fulfill 
        the expected output format.
        """
        required_minutes = int(duration.total_seconds() // 60)
        
        # Get all free gaps in the calendar
        all_gaps = self._get_all_gaps(person_list)
        
        available_start_ranges = []
        for gap_start, gap_end in all_gaps:
            gap_duration = self._minutes_between(gap_start, gap_end)
            
            # If the gap is big enough to hold the meeting
            if gap_duration >= required_minutes:
                earliest_start = gap_start
                
                # Calculate the absolute latest time a meeting can start within this gap
                # without exceeding the gap's end time.
                gap_end_minutes = gap_end.hour * 60 + gap_end.minute
                latest_start_minutes = gap_end_minutes - required_minutes
                latest_start = time(latest_start_minutes // 60, latest_start_minutes % 60)
                
                # Append the valid range of start times
                available_start_ranges.append(TimeSlot(earliest_start, latest_start))

        return available_start_ranges

    def find_max_available_slot(self, person_list: List[str]) -> Tuple[time, time, int]:
        """
        BONUS FEATURE (Fallback): 
        If the exact requested duration is not available, this function finds 
        the single longest available time slot to suggest an alternative.
        """
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
        """
        BONUS FEATURE (Bottleneck Analysis):
        Identifies who has the most scheduled meeting minutes. 
        This helps the user know who to mark as 'Optional' to free up the schedule.
        """
        # Dictionary to track total busy minutes for each requested person
        busy_minutes = {person: 0 for person in person_list}
        all_events = self._event_provider.get_events()
        
        for event in all_events:
            if event.person_name in busy_minutes:
                duration = self._minutes_between(event.time_slot.start_time, event.time_slot.end_time)
                busy_minutes[event.person_name] += duration
                
        # Return the person with the maximum meeting time
        busiest_person = max(busy_minutes.items(), key=lambda item: item[1])
        return busiest_person

    def _get_all_gaps(self, person_list: List[str]) -> List[Tuple[time, time]]:
        """
        Core Algorithm: Merge Overlapping Intervals.
        Time Complexity: O(N log N) due to sorting.
        Space Complexity: O(N) to store merged intervals.
        """
        all_events = self._event_provider.get_events()
        target_persons = set(person_list)
        
        # Filter events only for the requested attendees
        relevant_slots = [
            event.time_slot for event in all_events 
            if event.person_name in target_persons
        ]

        if not relevant_slots:
            return [(self.day_start, self.day_end)]

        # Step 1: Sort intervals by start time
        relevant_slots.sort(key=lambda slot: slot.start_time)
        
        # Step 2: Merge overlapping intervals to create solid blocks of busy time
        merged_slots = [TimeSlot(relevant_slots[0].start_time, relevant_slots[0].end_time)]
        for current in relevant_slots[1:]:
            last_merged = merged_slots[-1]
            if current.start_time <= last_merged.end_time:
                last_merged.end_time = max(last_merged.end_time, current.end_time)
            else:
                merged_slots.append(TimeSlot(current.start_time, current.end_time))

        # Step 3: Extract the free gaps between the busy blocks
        gaps = []
        if self._minutes_between(self.day_start, merged_slots[0].start_time) > 0:
            gaps.append((self.day_start, merged_slots[0].start_time))

        for i in range(len(merged_slots) - 1):
            gap_start = merged_slots[i].end_time
            gap_end = merged_slots[i+1].start_time
            if self._minutes_between(gap_start, gap_end) > 0:
                gaps.append((gap_start, gap_end))

        if self._minutes_between(merged_slots[-1].end_time, self.day_end) > 0:
            gaps.append((merged_slots[-1].end_time, self.day_end))

        return gaps

    def _minutes_between(self, start: time, end: time) -> int:
        """Helper to safely calculate minutes between two time objects."""
        if start >= end:
            return 0
        return (end.hour * 60 + end.minute) - (start.hour * 60 + start.minute)