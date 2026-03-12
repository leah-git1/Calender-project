import pytest
from datetime import time, timedelta
from typing import List

# Importing the core models and services from our application
from io_comp.models.domain import Event, TimeSlot
from io_comp.services.calendar_service import CalendarService

class MockEventProvider:
    """
    MOCKING / DEPENDENCY INJECTION:
    A mock data provider used exclusively for testing.
    Instead of reading from a real CSV file (which is slow and can break if the file changes),
    we inject this Mock class into our CalendarService. 
    It simply returns a hardcoded list of events that we define in each test.
    """
    def __init__(self, mock_events: List[Event]):
        self.mock_events = mock_events

    def get_events(self) -> List[Event]:
        """Returns the hardcoded events injected during test setup."""
        return self.mock_events


def test_no_events_whole_day_available():
    """
    TEST CASE 1: The "Best Case" Scenario (Empty Calendar).
    Goal: Verify that if a user has absolutely no meetings, the system 
    identifies the entire workday (starting at 07:00) as available.
    """
    # 1. SETUP: Create a mock provider with an empty list of events
    provider = MockEventProvider([])
    service = CalendarService(event_provider=provider)
    
    # 2. ACTION: Request a 60-minute meeting for Alice
    duration = timedelta(minutes=60)
    results = service.find_shared_available_slots(["Alice"], duration)
    
    # 3. ASSERT: 
    # - We expect exactly 1 block of available time.
    # - The start time of this block MUST be exactly 07:00 (start of the workday).
    assert len(results) == 1, "Should return exactly one massive time slot for the whole day."
    assert results[0].start_time == time(7, 0), "The available slot should start exactly at 07:00."


def test_no_shared_time_available():
    """
    TEST CASE 2: The "Worst Case" Edge Case (Fully Booked Day).
    Goal: Verify that the system correctly returns an empty list if the requested 
    users have completely overlapping schedules that block the entire day.
    """
    # 1. SETUP: 
    # Alice is busy the entire morning (07:00-14:00).
    # Jack is busy the entire afternoon (13:00-19:00).
    # Together, the entire workday is blocked. There is no shared free time.
    events = [
        Event(person_name="Alice", subject="Busy Morning", time_slot=TimeSlot(time(7, 0), time(14, 0))),
        Event(person_name="Jack", subject="Busy Afternoon", time_slot=TimeSlot(time(13, 0), time(19, 0)))
    ]
    provider = MockEventProvider(events)
    service = CalendarService(event_provider=provider)
    
    # 2. ACTION: Request a 2-hour meeting for both Alice and Jack
    duration = timedelta(hours=2)
    results = service.find_shared_available_slots(["Alice", "Jack"], duration)
    
    # 3. ASSERT: The resulting list MUST be empty (length 0).
    assert len(results) == 0, "Expected an empty list because there is no shared free time at all."


def test_standard_overlapping_meetings():
    """
    TEST CASE 3: Core Algorithm Test (Merge Overlapping Intervals).
    Goal: Verify that the algorithm correctly merges overlapping meetings
    between different users and correctly identifies the free gaps before and after.
    """
    # 1. SETUP:
    # Alice meets from 08:00 to 09:30. 
    # Jack meets from 09:00 to 10:00.
    # The algorithm should merge this into one solid busy block: 08:00 - 10:00.
    # Therefore, the expected free gaps are 07:00-08:00 and 10:00-19:00.
    events = [
        Event("Alice", "Meeting A", TimeSlot(time(8, 0), time(9, 30))),
        Event("Jack", "Meeting B", TimeSlot(time(9, 0), time(10, 0)))
    ]
    provider = MockEventProvider(events)
    service = CalendarService(event_provider=provider)
    
    # 2. ACTION: Request a 60-minute meeting
    duration = timedelta(minutes=60)
    results = service.find_shared_available_slots(["Alice", "Jack"], duration)
    
    # We extract just the start times from the TimeSlot objects to make assertions cleaner
    start_times = [slot.start_time for slot in results]
    
    # 3. ASSERT: We check that 07:00 and 10:00 are successfully identified as valid start times.
    assert time(7, 0) in start_times, "07:00 should be an available start time (before the merged block)."
    assert time(10, 0) in start_times, "10:00 should be an available start time (after the merged block)."


def test_find_busiest_person_bottleneck():
    """
    TEST CASE 4: Bonus Feature Test (Bottleneck Analysis).
    Goal: Verify that the analytics function correctly calculates the total meeting
    minutes for each person and correctly identifies the one with the highest total.
    """
    # 1. SETUP: 
    # Alice has 1 hour of meetings. 
    # Jack has 2 separate 1-hour meetings (Total 2 hours).
    events = [
        Event("Alice", "Quick Sync", TimeSlot(time(8, 0), time(9, 0))),   # 60 mins
        Event("Jack", "Deep Work", TimeSlot(time(9, 0), time(10, 0))),    # 60 mins
        Event("Jack", "Client Call", TimeSlot(time(14, 0), time(15, 0)))  # 60 mins
    ]
    provider = MockEventProvider(events)
    service = CalendarService(event_provider=provider)
    
    # 2. ACTION: Ask the service who is the busiest between Alice and Jack
    busiest_name, busiest_mins = service.find_busiest_person(["Alice", "Jack"])
    
    # 3. ASSERT: The system must identify Jack, with exactly 120 minutes of meetings.
    assert busiest_name == "Jack", "The system should identify Jack as the bottleneck."
    assert busiest_mins == 120, "Jack's total meeting time should be exactly 120 minutes."