from flask import Flask
from flask_mysqldb import MySQL
import MySQLdb.cursors

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your-very-secret-key'

# Configure MySQL connection
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'timetable_attendance'

# Initialize MySQL
mysql = MySQL(app)

def create_and_populate_table():
    with app.app_context():
        cur = mysql.connection.cursor()

        # Create the table if it doesn't exist
        create_table_query = """
        CREATE TABLE IF NOT EXISTS student_timetable_reports (
            ReportID INT AUTO_INCREMENT PRIMARY KEY,
            StudentID INT NOT NULL,
            SemesterID INT NOT NULL,
            ProgramID INT NOT NULL,
            CourseID INT NOT NULL,
            FacultyID INT NOT NULL,
            DayOfWeek VARCHAR(20) NOT NULL,
            SlotID INT NOT NULL,
            RoomID INT NOT NULL,
            CourseName VARCHAR(255) NOT NULL,
            FacultyName VARCHAR(255) NOT NULL,
            RoomNumber VARCHAR(50) NOT NULL,
            StartTime TIME NOT NULL,
            EndTime TIME NOT NULL,
            CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (StudentID) REFERENCES students(StudentID),
            FOREIGN KEY (SemesterID) REFERENCES semesters(SemesterID),
            FOREIGN KEY (ProgramID) REFERENCES offered_programs(ProgramID),
            FOREIGN KEY (CourseID) REFERENCES courses(CourseID),
            FOREIGN KEY (FacultyID) REFERENCES faculty(FacultyID),
            FOREIGN KEY (SlotID) REFERENCES time_slots(SlotID),
            FOREIGN KEY (RoomID) REFERENCES rooms(RoomID)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        cur.execute(create_table_query)

        # Clear existing data
        cur.execute("DELETE FROM student_timetable_reports")

        # Populate the table with data from schedule, students, etc.
        populate_query = """
        INSERT INTO student_timetable_reports
        (StudentID, SemesterID, ProgramID, CourseID, FacultyID, DayOfWeek, SlotID, RoomID, CourseName, FacultyName, RoomNumber, StartTime, EndTime)
        SELECT
            s.StudentID,
            cs.SemesterID,
            op.ProgramID,
            sch.CourseID,
            sch.FacultyID,
            sch.DayOfWeek,
            sch.SlotID,
            sch.RoomID,
            c.CourseName,
            CONCAT(f.FirstName, ' ', f.LastName) as FacultyName,
            r.RoomNumber,
            ts.StartTime,
            ts.EndTime
        FROM students s
        JOIN assign_courses_to_student acs ON s.StudentID = acs.StudentID
        JOIN current_semester cs ON acs.CurrentSemesterID = cs.CurrentSemesterID
        JOIN offered_programs op ON acs.ProgramID = op.ProgramID
        JOIN schedule sch ON sch.ProgramID = op.ProgramID AND sch.SemesterID = cs.SemesterID
        JOIN courses c ON sch.CourseID = c.CourseID
        JOIN faculty f ON sch.FacultyID = f.FacultyID
        JOIN rooms r ON sch.RoomID = r.RoomID
        JOIN time_slots ts ON sch.SlotID = ts.SlotID
        WHERE acs.CourseID = sch.CourseID
        """
        cur.execute(populate_query)

        mysql.connection.commit()
        cur.close()
        print("Table created and populated successfully!")

if __name__ == '__main__':
    create_and_populate_table()
