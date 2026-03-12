# 📅 Smart Calendar Search Engine

An advanced, object-oriented calendar search engine designed to find optimal meeting times for multiple attendees. Built with a focus on **SOLID principles**, **clean architecture**, and a **product-minded** user experience.

---

## 🎯 The Challenge (Original Requirements)

The core objective of this assignment was to build a system that:

1. Takes a list of people and a desired meeting duration.
2. Reads calendar events from a provided `calendar.csv` file.
3. Finds all available shared time slots within a single workday (07:00 - 19:00).
4. Outputs the available times exactly as specified in the assignment examples.

**Code Quality Requirements:**

* Modular and decoupled Object-Oriented Design (SOLID).
* Meaningful naming conventions.
* Comprehensive Unit Testing.

---

## 🏗️ Architecture & Design Decisions

To ensure the system is highly maintainable, testable, and scalable, several key architectural decisions were made:

### 1. Layered Architecture & Dependency Injection

The system is divided into clear layers (`models`, `data`, `services`).

I introduced an `EventProvider` Protocol (Interface). The `CalendarService` does not know about CSV files; it simply expects an object that provides events. This decoupling allows us to easily swap the CSV file with a Database or a Mock API in the future without changing the core algorithm.

### 2. Domain Modeling (Tackling Vague Requirements)

The original spec requested a `List[time]` return type. However, the expected output example clearly showed continuous time ranges (e.g., `"09:40 - 12:00"`). Since a single `time` object cannot represent a duration range, I leveraged the assignment's permission to interpret requirements and upgraded the return type to `List[TimeSlot]`. This accurately models the domain and perfectly matches the expected output format.

### 3. Algorithm: Interval Merging

Instead of checking availability minute-by-minute (which is highly inefficient), the system uses a **Merge Intervals Algorithm**:

1. Filters events for the requested attendees.
2. Sorts the events by start time.
3. Merges overlapping events to create solid "blocks" of busy time.
4. Extracts the free gaps between these blocks.

**Time Complexity:** `O(N log N)` due to the sorting phase.

---

## 🚀 "Product-Minded" Bonus Features

Beyond the core requirements, I approached this project as a Product Engineer and added features to solve real-world scheduling frustrations:

* **💡 Smart Fallback (Max Available Slot):** If a user requests a 3-hour meeting but the team only has 1 hour available, a standard system simply fails. This system catches the failure and automatically suggests the longest common free time available that day.

* **📊 Bottleneck Analysis:** If a meeting cannot be scheduled, the system analyzes the data to identify the "Bottleneck" (the person with the most meeting minutes) and suggests making them 'Optional'.

* **🛑 Fail-Fast Mechanism:** Introduced a custom `EventProviderError`. If the data file is missing or corrupted, the system halts immediately rather than failing silently and risking double-bookings.

* **💻 Dynamic CLI:** Integrated Python's `argparse` to allow users to query the calendar dynamically directly from the terminal, avoiding hardcoded variables.

---

## 💻 Getting Started / How to Run

The application features a robust Command Line Interface (CLI). You do not need to modify the code to run different scenarios.

### Prerequisites

* Python 3.8+

### Standard Search (Matching the Example)

To find a 60-minute slot for Alice and Jack:

```bash
python -m io_comp.app --people Alice Jack --duration 60
```

**Expected Output:**

```
Starting Time of available slots: 07:00
Starting Time of available slots: 09:40 - 12:00
Starting Time of available slots: 14:00 - 15:00
Starting Time of available slots: 17:00 - 18:00
```

### Triggering the Smart Fallback & Analytics

Try scheduling an impossibly long meeting (e.g., 3 hours for Alice, Jack, and Bob) to see the bonus features in action:

```bash
python -m io_comp.app --people Alice Jack Bob --duration 180
```

**Expected Output:**

```
❌ No 180-minute slots available.
🔍 Searching for alternatives...

💡 SMART SUGGESTION: Longest common free time:
   👉 60 minutes (Between 11:30 and 12:30)

📊 BOTTLENECK ANALYSIS:
   Jack is the busiest person (4.5 hrs of meetings).
   Consider making Jack 'Optional'.
```

---

## 🧪 Testing

The project includes a comprehensive test suite using pytest. Tests use a MockEventProvider (Dependency Injection) to ensure tests run fast and deterministically without relying on the external CSV file.

### Running Tests

```bash
pytest -v
```

### Test Coverage Includes:

* **test_no_events_whole_day_available:** The best-case scenario (Empty calendar).
* **test_no_shared_time_available:** The worst-case edge case (Fully blocked day).
* **test_standard_overlapping_meetings:** Verifies the core Interval Merging algorithm.
* **test_find_busiest_person_bottleneck:** Verifies the accuracy of the Bottleneck Analytics engine.

---

## 📁 Project Structure

```
python-project/
├── io_comp/
│   ├── models/          # Domain models (Event, TimeSlot)
│   ├── data/            # Data providers (CSV, Mock)
│   ├── services/        # Business logic (CalendarService)
│   └── app.py           # CLI entry point
├── tests/               # Unit tests
├── calendar.csv         # Sample data
└── README.md
```

---

## 🎓 Key Takeaways

* **SOLID Principles:** Dependency Injection, Single Responsibility, Open/Closed.
* **Algorithm Efficiency:** O(N log N) interval merging vs. brute force.
* **Product Thinking:** Smart fallbacks and analytics enhance user experience.
* **Testability:** Protocol-based design enables easy mocking and testing.



