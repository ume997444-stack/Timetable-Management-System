-- SQL script to create weekly timetable view or table if needed
-- Based on existing tables: schedule, time_slots, rooms, semesters, programs, sessions

-- No new table needed as schedule table contains necessary info
-- Create a view to simplify weekly timetable queries (optional)

CREATE OR REPLACE VIEW weekly_timetable_view AS
SELECT 
    s.ScheduleID,
    s.SemesterID,
    s.ProgramID,
    ts.DayOfWeek,
    ts.StartTime,
    ts.EndTime,
    r.RoomNumber,
    c.CourseName,
    f.FirstName AS FacultyFirstName,
    f.LastName AS FacultyLastName
FROM schedule s
JOIN time_slots ts ON s.SlotID = ts.SlotID
JOIN rooms r ON s.RoomID = r.RoomID
JOIN offered_courses oc ON s.OfferedCourseID = oc.OfferedCourseID
JOIN courses c ON oc.CourseID = c.CourseID
JOIN faculty f ON s.FacultyID = f.FacultyID;

-- This view can be used to query timetable by day, time, semester, program, session etc.
