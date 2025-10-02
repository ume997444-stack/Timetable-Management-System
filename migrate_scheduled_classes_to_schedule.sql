-- Migration script to copy data from scheduled_classes to schedule table

INSERT INTO schedule (CourseID, FacultyID, RoomID, SlotID, DayOfWeek, SemesterID, ProgramID)
SELECT 
    sc.CourseID,
    sc.FacultyID,
    sc.RoomID,
    sc.SlotID,
    sc.DayOfWeek,
    -- Assuming default SemesterID and ProgramID as 1, adjust if needed
    1 AS SemesterID,
    1 AS ProgramID
FROM scheduled_classes sc;

-- Drop the scheduled_classes table after migration
DROP TABLE IF EXISTS scheduled_classes;
