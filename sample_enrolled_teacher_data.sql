-- Add Department
INSERT INTO departments (DepartmentName) VALUES ('Computer Science');

-- Add Program
INSERT INTO programs (ProgramName) VALUES ('BSCS');

-- Add Course
INSERT INTO courses (CourseName, CourseCode, Credits) VALUES ('Database Systems', 'CS301', 3);

-- Add Semester
INSERT INTO semesters (SemesterName) VALUES ('Fall 2025');

-- Add Faculty
INSERT INTO faculty (FirstName, LastName, Email, password, DepartmentID)
VALUES ('Ali', 'Khan', 'ali.khan@example.com', 'password123', 1);

-- Add Offered Course (linking course, semester, program)
INSERT INTO offered_courses (CourseID, SemesterID, ProgramID)
VALUES (1, 1, 1);

-- Add Offered Teacher (linking faculty and offered course)
INSERT INTO offered_teachers (FacultyID, OfferedCourseID)
VALUES (1, 1);
