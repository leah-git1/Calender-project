import os
import sys  # Added to allow graceful system exit on critical errors
import logging
import argparse
from typing import List
from datetime import time, timedelta

from io_comp.models.domain import TimeSlot
from io_comp.data.event_provider import CsvEventProvider
from io_comp.services.calendar_service import CalendarService
from io_comp.data.event_provider import EventProviderError

# Configure logging to display clean, professional terminal output
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def get_calendar_service() -> CalendarService:
    """Helper to initialize the service with the CSV provider (Dependency Injection)."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(base_dir, 'resources', 'calendar.csv')
    return CalendarService(event_provider=CsvEventProvider(csv_path))

def find_available_slots(person_list: List[str], event_duration: timedelta) -> List[TimeSlot]:
    """
    Entry point function.
    Upgraded to return List[TimeSlot] to accurately support the required example output.
    """
    service = get_calendar_service()
    return service.find_shared_available_slots(person_list, event_duration)

def main():
    """
    Application Entry Point.
    Features CLI arguments, dynamic output formatting, and smart fallback mechanisms.
    """
    # --- 1. CLI Setup ---
    parser = argparse.ArgumentParser(description="Find shared calendar slots for a team.")
    parser.add_argument('--people', nargs='+', required=True, help="List of attendees")
    parser.add_argument('--duration', type=int, required=True, help="Meeting duration in minutes")
    
    args = parser.parse_args()
    people = args.people
    duration = timedelta(minutes=args.duration) 
    
    # Wrap the core logic in a try-except block to prevent "Silent Failures" 
    # if the CSV file is missing or corrupted.
    try:
        # --- 2. Core Search & Exact Output Formatting ---
        results = find_available_slots(people, duration)
        
        if results:
            for slot in results:
                # Matches EXACTLY the requested output format in the assignment
                # E.g., "07:00" if no range exists, or "09:40 - 12:00" if a range is possible.
                if slot.start_time == slot.end_time:
                    logger.info(f"Starting Time of available slots: {slot.start_time.strftime('%H:%M')}")
                else:
                    logger.info(f"Starting Time of available slots: {slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}")
                
        else:
            # --- 3. Fallback Logic ---
            logger.warning(f"❌ No {args.duration}-minute slots available.")
            logger.info("🔍 Searching for alternatives...\n")
            
            service = get_calendar_service()
            best_start, best_end, max_mins = service.find_max_available_slot(people)
            
            if max_mins > 0:
                logger.info("💡 SMART SUGGESTION: Longest common free time:")
                logger.info(f"   👉 {max_mins} minutes (Between {best_start.strftime('%H:%M')} and {best_end.strftime('%H:%M')})\n")
            
            # --- 4. Bottleneck Analysis ---
            if len(people) > 1:
                busiest_name, busiest_mins = service.find_busiest_person(people)
                busiest_hours = round(busiest_mins / 60, 1)
                logger.info("📊 BOTTLENECK ANALYSIS:")
                logger.info(f"   {busiest_name} is the busiest person ({busiest_hours} hrs of meetings).")
                logger.info(f"   Consider making {busiest_name} 'Optional'.")

    except EventProviderError as e:
        # --- 5. Fail-Fast Error Handling ---
        # Catches the custom exception raised by the CsvEventProvider.
        # Halts the system immediately to prevent double-booking on a presumed "empty" calendar.
        logger.error("\n🚨 SYSTEM HALTED DUE TO DATA ERROR 🚨")
        logger.error(str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()