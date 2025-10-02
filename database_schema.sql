-- Database Schema for Timetable Attendance System
-- Run this script in XAMPP MySQL to create the database and tables

-- Create database
CREATE DATABASE IF NOT EXISTS timetable_attendance;
USE timetable_attendance;

-- Departments table
CREATE TABLE IF NOT EXISTS departments (
    DepartmentID INT AUTO_INCREMENT PRIMARY KEY,
    DepartmentName VARCHAR(255) NOT NULL
);

-- Faculty table
CREATE TABLE IF NOT EXISTS faculty (
    FacultyID INT AUTO_INCREMENT PRIMARY KEY,
    FirstName VARCHAR(255),
    LastName VARCHAR(255),
    Email VARCHAR(255),
    password VARCHAR(255),
    DepartmentID INT,
    FOREIGN KEY (DepartmentID) REFERENCES departments(DepartmentID)
);

-- Students table
CREATE TABLE IF NOT EXISTS students (
    StudentID INT AUTO_INCREMENT PRIMARY KEY,
    FirstName VARCHAR(255),
    LastName VARCHAR(255),
    EnrollmentNo VARCHAR(255),
    Email VARCHAR(255),
    password VARCHAR(255),
    DepartmentID INT,
    FOREIGN KEY (DepartmentID) REFERENCES departments(DepartmentID)
);

-- Courses table
CREATE TABLE IF NOT EXISTS courses (
    CourseID INT AUTO_INCREMENT PRIMARY KEY,
    CourseName VARCHAR(255),
    DepartmentID INT,
    FacultyID INT,
    FOREIGN KEY (DepartmentID) REFERENCES departments(DepartmentID),
    FOREIGN KEY (FacultyID) REFERENCES faculty(FacultyID)
);

-- Semesters table
CREATE TABLE IF NOT EXISTS semesters (
    SemesterID INT AUTO_INCREMENT PRIMARY KEY,
    SemesterName VARCHAR(255),
    Email VARCHAR(255),
    Password VARCHAR(255)
);

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    SessionID INT AUTO_INCREMENT PRIMARY KEY,
    StartYear INT,
    EndYear INT
);

-- Offered Programs table
CREATE TABLE IF NOT EXISTS offered_programs (
    ProgramID INT AUTO_INCREMENT PRIMARY KEY,
    ProgramName VARCHAR(255),
    SessionID INT,
    DepartmentID INT,
    FOREIGN KEY (SessionID) REFERENCES sessions(SessionID),
    FOREIGN KEY (DepartmentID) REFERENCES departments(DepartmentID)
);

-- Offered Courses table
CREATE TABLE IF NOT EXISTS offered_courses (
    OfferedCourseID INT AUTO_INCREMENT PRIMARY KEY,
    CourseID INT,
    SemesterID INT,
    DepartmentID INT,
    FOREIGN KEY (CourseID) REFERENCES courses(CourseID),
    FOREIGN KEY (SemesterID) REFERENCES semesters(SemesterID),
    FOREIGN KEY (DepartmentID) REFERENCES departments(DepartmentID)
);

-- Offered Teachers table
CREATE TABLE IF NOT EXISTS offered_teachers (
    OfferedTeacherID INT AUTO_INCREMENT PRIMARY KEY,
    FacultyID INT,
    OfferedCourseID INT,
    DepartmentID INT,
    ProgramID INT,
    FOREIGN KEY (FacultyID) REFERENCES faculty(FacultyID),
    FOREIGN KEY (OfferedCourseID) REFERENCES offered_courses(OfferedCourseID),
    FOREIGN KEY (DepartmentID) REFERENCES departments(DepartmentID),
    FOREIGN KEY (ProgramID) REFERENCES offered_programs(ProgramID)
);

-- Enrolled Students table
CREATE TABLE IF NOT EXISTS enrolledstudents (
    EnrollmentID INT AUTO_INCREMENT PRIMARY KEY,
    StudentID INT,
    CourseID INT,
    SemesterID INT,
    FOREIGN KEY (StudentID) REFERENCES students(StudentID),
    FOREIGN KEY (CourseID) REFERENCES courses(CourseID),
    FOREIGN KEY (SemesterID) REFERENCES semesters(SemesterID)
);

-- Rooms table
CREATE TABLE IF NOT EXISTS rooms (
    RoomID INT AUTO_INCREMENT PRIMARY KEY,
    RoomNumber VARCHAR(255)
);

-- Time Slots table
CREATE TABLE IF NOT EXISTS time_slots (
    SlotID INT AUTO_INCREMENT PRIMARY KEY,
    StartTime TIME,
    EndTime TIME
);

-- Schedule table
CREATE TABLE IF NOT EXISTS schedule (
    ScheduleID INT AUTO_INCREMENT PRIMARY KEY,
    CourseID INT,
    FacultyID INT,
    RoomID INT,
    SlotID INT,
    DayOfWeek VARCHAR(255),
    SemesterID INT,
    ProgramID INT,
    FOREIGN KEY (CourseID) REFERENCES courses(CourseID),
    FOREIGN KEY (FacultyID) REFERENCES faculty(FacultyID),
    FOREIGN KEY (RoomID) REFERENCES rooms(RoomID),
    FOREIGN KEY (SlotID) REFERENCES time_slots(SlotID),
    FOREIGN KEY (SemesterID) REFERENCES semesters(SemesterID),
    FOREIGN KEY (ProgramID) REFERENCES offered_programs(ProgramID)
);

-- Attendance table
CREATE TABLE IF NOT EXISTS attendance (
    AttendanceID INT AUTO_INCREMENT PRIMARY KEY,
    StudentID INT,
    CourseID INT,
    AttendanceDate DATE,
    AttendanceStatus VARCHAR(255),
    FOREIGN KEY (StudentID) REFERENCES students(StudentID),
    FOREIGN KEY (CourseID) REFERENCES courses(CourseID)
);

-- Timetables table (legacy)
CREATE TABLE IF NOT EXISTS timetables (
    TimetableID INT AUTO_INCREMENT PRIMARY KEY,
    CourseID INT,
    DayOfWeek VARCHAR(255),
    StartTime TIME,
    EndTime TIME,
    RoomNumber VARCHAR(255),
    TaughtBy INT,
    FOREIGN KEY (CourseID) REFERENCES courses(CourseID),
    FOREIGN KEY (TaughtBy) REFERENCES faculty(FacultyID)
);

-- Current Semester table
CREATE TABLE IF NOT EXISTS current_semester (
    CurrentSemesterID INT AUTO_INCREMENT PRIMARY KEY,
    ProgramID INT,
    SemesterID INT,
    StartDate DATE,
    EndDate DATE,
    FOREIGN KEY (ProgramID) REFERENCES offered_programs(ProgramID),
    FOREIGN KEY (SemesterID) REFERENCES semesters(SemesterID)
);

-- Assign Courses to Student table
CREATE TABLE IF NOT EXISTS assign_courses_to_student (
    AssignID INT AUTO_INCREMENT PRIMARY KEY,
    StudentID INT,
    ProgramID INT,
    SessionID INT,
    CurrentSemesterID INT,
    CourseID INT,
    Allowed VARCHAR(255),
    Is_Repeater VARCHAR(255),
    FOREIGN KEY (StudentID) REFERENCES students(StudentID),
    FOREIGN KEY (ProgramID) REFERENCES offered_programs(ProgramID),
    FOREIGN KEY (SessionID) REFERENCES sessions(SessionID),
    FOREIGN KEY (CurrentSemesterID) REFERENCES current_semester(CurrentSemesterID),
    FOREIGN KEY (CourseID) REFERENCES courses(CourseID)
);

-- Admin table
CREATE TABLE IF NOT EXISTS admin (
    AdminID INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255),
    password VARCHAR(255)
);

-- Insert sample admin user
INSERT INTO admin (username, password) VALUES ('admin', 'admin123') ON DUPLICATE KEY UPDATE password = 'admin123';
