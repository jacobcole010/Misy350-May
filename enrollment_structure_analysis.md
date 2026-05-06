# Enrollment Manager Design Analysis

## Method Map Overview

Based on the initial categorization and reflections, the codebase is organized into the following layers:

### Constants & Configuration
- DB_PATH, SNAPSHOT_PATH, statuses, current_student → **Single Task, Self-Contained, Constants/Config**
- AVAILABLE_COURSE_KEYS list → **Single Task, Self-Contained, Constants/Config**

### Database Layer
- connect → **Single Task, Self-Contained, Database Class**
- create_tables → **Single Task, Requires Passing State, Database Class**
- seed_sample_data → **Single Task, Requires Passing State, Database Class**
- get_available_course_keys → **Single Task, Requires Passing State, Database Class**
- get_course_by_key → **Single Task, Requires Passing State, Database Class**
- get_student_enrollments → **Single Task, Requires Passing State, Database Class**
- get_student_enrollment_history → **Single Task, Requires Passing State, Database Class**
- get_all_enrollment_records → **Single Task, Requires Passing State, Database Class**
- SQLite SELECT, INSERT, UPDATE → **Single Task, Requires Passing State, Database Class**

### Service Layer
- enroll_with_key → **Mixed (Same Layer), Requires Passing State, Service Class**
- soft_unenroll_student → **Single Task, Requires Passing State, Service Class**
- get_student_summary → **Mixed (Same Layer), Requires Passing State, Service Class**
- export_database_snapshot / JSON writing → **Mixed (Same Layer), Reads Global State, Service Class**

### Top-Level Orchestration
- main runner / top-level test flow → **Mixed (Cross Layer), Reads Global State, Service Class**

---

## Key Design Issues

### 1. soft_unenroll_student Should Move to Database Class

**Current Status:** Marked as Service Class

**Issue:** Looking at the implementation, `soft_unenroll_student` is purely a SQL UPDATE statement wrapped in a function. It doesn't contain business logic—it directly mutates the database.

**Why It Matters:** Keeping all data mutations (INSERT, UPDATE, DELETE) in the Database layer maintains clean layer separation. The Service layer should orchestrate and make decisions, not execute raw database operations.

**Impact:** If this stays in Service, you blur the line between where business decisions are made and where data actually changes.

---

### 2. enroll_with_key and get_student_summary Are Actually Cross Layer

**Current Status:** Marked as Mixed (Same Layer)

**Issue:** Both functions call Database layer functions and then orchestrate the results:
- `enroll_with_key` calls `get_course_by_key()` (Database) and then executes an INSERT
- `get_student_summary` calls `get_student_enrollment_history()` (Database) and aggregates the results

**Why It Matters:** This is layer crossing, not same-layer mixing. Your Service layer is directly dependent on Database layer structure and availability.

**Impact:** If you need to refactor the Database layer, these Service functions may break. It also makes testing difficult because Service depends on working Database implementations.

---

### 3. export_database_snapshot Mixes Too Many Concerns

**Current Status:** Mixed (Same Layer), but actually does more

**Issue:** This function:
1. Reads global state (`CURRENT_STUDENT`)
2. Calls multiple Database functions (`get_available_course_keys()`, `get_all_enrollment_records()`)
3. Handles file I/O (writes JSON to disk)
4. Orchestrates data aggregation

**Why It Matters:** This violates single responsibility. It's not just orchestration—it's also handling presentation (JSON structure) and I/O concerns.

**Impact:** This function is hard to test and hard to reuse. If you want to export in a different format, you can't reuse the data-gathering logic without refactoring.

---

### 4. Inconsistent State Passing Pattern

**Current Status:** `connect()` is Self-Contained, but everything else "Requires Passing State"

**Issue:** Every Database function depends on the connection created by `connect()`, but they don't explicitly show this dependency. Each function opens its own connection with `with connect()` inside the function body.

**Why It Matters:** There's a hidden dependency chain that makes the architecture unclear:
- Every DB function must call `connect()`
- `connect()` must successfully access `DB_PATH`
- If connection management changes, all DB functions need updates

**Impact:** Connection lifecycle isn't centralized. You can't easily switch to connection pooling, mock connections for testing, or handle connection errors globally.

---

### 5. Layer Isolation Is Incomplete

**Current Status:** main → Service → Database → SQL

**Issue:** The layers can be traversed, but they're not truly isolated:
- Service functions directly call Database functions
- Service functions read global constants
- main() ties everything together without abstraction

**Why It Matters:** Your Database layer can't be swapped or mocked independently of the Service layer. Changes to Database function signatures force changes in Service callers.

**Impact:** Testing Service logic in isolation is difficult because you must either mock all Database functions or use a test database. Refactoring the Database layer becomes expensive.

---

## Recommendations for Before Implementation

1. **Move `soft_unenroll_student` to Database Class** — This is a database operation, not service logic.

2. **Clarify the Service-Database contract** — Decide if Service functions should:
   - Call Database functions directly (current approach), or
   - Use a Repository/Data Access Object pattern to mediate access

3. **Separate concerns in export_database_snapshot** — Split data gathering from JSON formatting:
   - Database layer: Provide query functions
   - Service layer: Aggregate and structure data
   - Separate function: Handle file I/O

4. **Consider centralizing connection management** — Either inject connection into functions or use a connection manager object to make dependencies explicit.

5. **Define layer contracts clearly** — Document what each layer can and cannot do before refactoring into classes.

---

## Next Steps

These issues should be resolved at the design level before you start implementing the class-based architecture. Focus on clarifying layer boundaries and responsibilities, not on writing code yet.
