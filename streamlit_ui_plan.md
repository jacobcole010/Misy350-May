# Streamlit UI Plan: Student Enrollment Dashboard

## App Structure & Imports

The app will import the backend module (`enrollment_starter.py`) to access service functions and the `CURRENT_STUDENT` constant. The main Streamlit app (`app.py`) will manage routing, session state, and UI rendering.

```
app.py imports:
- from enrollment_starter import (CURRENT_STUDENT, get_student_enrollments, 
  get_course_by_key, enroll_with_key, soft_unenroll_student, get_student_course_record)
```

## Session State Initialization

The app initializes session state keys on first load:

- `page`: Current page ("dashboard" or "class_detail"); default: "dashboard"
- `selected_course_id`: The course_id of the class being viewed; default: None
- `feedback_message`: User-facing status message; default: ""
- `feedback_type`: Message type ("success", "error", "warning"); default: ""

At app startup, check if these keys exist in `st.session_state` and initialize them if missing.

## Page Routing Logic

The app checks `st.session_state.page` to determine which page to render:

1. **If page == "dashboard"**: Render the dashboard with enrolled classes and enrollment form
2. **If page == "class_detail"**: Render the class detail page with course information

Navigation is controlled by updating `st.session_state.page` when the user clicks buttons.

## Dashboard Page Layout (Page 1)

**Header:**
- `st.title("Student Dashboard")`
- `st.write(f"Welcome, {CURRENT_STUDENT['name']}")`

**Enrolled Classes Section:**
- Use `st.subheader("Your Enrolled Classes")`
- Call `get_student_enrollments(CURRENT_STUDENT['user_id'])` to fetch enrolled courses
- If no courses, display: `st.info("You're not enrolled in any classes yet. Enter an enrollment key to enroll.")`
- If courses exist, use `st.columns()` to create card-style displays for each course
- Each card should show: course_name, instructor, enrolled_at
- Add two buttons per card: "Go to Class" and "Unenroll"
  - "Go to Class" button: Sets `selected_course_id = course_id`, sets `page = "class_detail"`, re-runs app
  - "Unenroll" button: Calls `soft_unenroll_student(user_id, course_id)`, sets feedback to success, clears feedback after display, refreshes the enrolled classes list

**Enrollment Key Entry Section:**
- Use `st.subheader("Enroll in a New Class")`
- `st.text_input("Enter enrollment key:")` to capture the key
- `st.button("Enroll")` to submit
- On button click:
  - Call `get_course_by_key(enrollment_key)` to validate the key
  - If valid: Call `enroll_with_key(user_id, email, enrollment_key)`, set feedback_message to "Successfully enrolled in [course_name]!", set feedback_type to "success"
  - If invalid: Set feedback_message to "Enrollment key not found. Please check and try again.", set feedback_type to "error"
  - Clear the text input after submission

**Feedback Area:**
- Display feedback based on `feedback_type`:
  - `st.success(feedback_message)` if feedback_type == "success"
  - `st.error(feedback_message)` if feedback_type == "error"
  - `st.warning(feedback_message)` if feedback_type == "warning"
- After displaying, immediately clear feedback_message and feedback_type to prevent persistence

## Class Detail Page Layout (Page 2)

**Header:**
- `st.title(f"{selected_course['course_name']}")`
- `st.write(f"Instructor: {selected_course['instructor']}")`

**Class Information:**
- Fetch the selected course's enrollment record using `get_student_course_record(CURRENT_STUDENT['user_id'], selected_course_id)`
- Fetch the course details by looking up the course information from the enrollment record
- Display using `st.columns(2)`:
  - Column 1: `st.metric("Course ID", course_id)`
  - Column 2: `st.metric("Enrolled Since", enrolled_at)`

**Action Area:**
- `st.button("Back to Dashboard")`: Sets `page = "dashboard"`, clears `selected_course_id`, re-runs app

## Feedback Messages

**Success:**
- Enrollment: "Successfully enrolled in {course_name}!"
- Unenroll: "You have unenrolled from {course_name}. You can re-enroll anytime."
- Display with `st.success()`

**Error:**
- Invalid key: "Enrollment key not found. Please check and try again."
- Backend error: "Unable to process your request. Please try again."
- Display with `st.error()`

**Warning:**
- Optional: confirmation messages before destructive actions
- Display with `st.warning()`

Messages should be displayed and cleared on the next action or page navigation.

## Data Flow: UI Calling Backend Functions

1. **On load:** Fetch enrolled classes via `get_student_enrollments(user_id)`
2. **Enrollment action:**
   - Validate key via `get_course_by_key(enrollment_key)`
   - If valid, call `enroll_with_key(user_id, email, enrollment_key)`
   - Set feedback and refresh enrolled classes list
3. **Navigate to class:** Set `selected_course_id` and change `page` to "class_detail"
4. **Unenroll action:**
   - Call `soft_unenroll_student(user_id, course_id)`
   - Set success feedback
   - Refresh enrolled classes list
5. **Back to dashboard:** Set `page = "dashboard"`, clear `selected_course_id`, re-run

## Session State Summary

| Key | Type | Purpose | Set On |
|-----|------|---------|--------|
| `page` | str | Current page ("dashboard" or "class_detail") | Navigation buttons |
| `selected_course_id` | str or None | Course ID being viewed | "Go to Class" button or "Back" button |
| `feedback_message` | str | Message to display | After enrollment/unenroll actions |
| `feedback_type` | str | Type of message (success/error/warning) | After enrollment/unenroll actions |

## App Flow Summary

1. User opens app → Dashboard loads with enrolled classes
2. User enters enrollment key and clicks "Enroll" → Backend validates and enrolls, feedback message shown, enrolled classes refreshed
3. User clicks "Go to Class" → Page 2 loads with class details
4. User clicks "Back to Dashboard" → Returns to Page 1
5. User clicks "Unenroll" → Soft-unenroll called, feedback shown, enrolled classes refreshed