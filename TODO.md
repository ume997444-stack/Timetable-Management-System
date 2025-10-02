# Role-Based Access Control Implementation Plan

## Information Gathered
- Current app has session-based access with roles: 'admin', 'teacher', 'student'
- @app.before_request checks role and restricts access:
  - Students: only student_timetable, logout, static
  - Teachers: only faculty_timetable, logout, static
  - Admins: all access
- Most CRUD routes are implicitly admin-only due to restrictions
- Login sets session['role'] based on user type

## Plan
- Add a `role_required` decorator for explicit role checking
- Apply decorator to routes for granular control
- Keep @app.before_request for basic restrictions
- Ensure decorators align with existing logic

## Dependent Files to Edit
- app.py: Add decorator and apply to routes

## Followup Steps
- Test login and access for each role
- Verify redirects work correctly
- Check for any missing restrictions
