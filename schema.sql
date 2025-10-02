-- Run this SQL in your MySQL database to create the necessary tables

-- Create the 'schedule' table for class/faculty timetable management
CREATE TABLE IF NOT EXISTS schedule (
    ScheduleID INT AUTO_INCREMENT PRIMARY KEY,
    CourseID INT NOT NULL,
    FacultyID INT NOT NULL,
    RoomID INT NOT NULL,
    SlotID INT NOT NULL,
    DayOfWeek VARCHAR(10) NOT NULL,
    SemesterID INT NOT NULL,
    ProgramID INT NOT NULL,
    FOREIGN KEY (CourseID) REFERENCES courses(CourseID),
    FOREIGN KEY (FacultyID) REFERENCES faculty(FacultyID),
    FOREIGN KEY (RoomID) REFERENCES rooms(RoomID),
    FOREIGN KEY (SlotID) REFERENCES time_slots(SlotID),
    FOREIGN KEY (SemesterID) REFERENCES semesters(SemesterID),
    FOREIGN KEY (ProgramID) REFERENCES offered_programs(ProgramID)

    FOREIGN KEY (ProgramID) REFERENCES offered_programs(ProgramID)
);
