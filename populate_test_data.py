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

def populate_test_data():
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
            CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        cur.execute(create_table_query)

        # Clear existing data
        cur.execute("DELETE FROM student_timetable_reports")

        # Insert test data
        test_data = [
            (4, 3, 2, 3, 2, 'Monday', 8, 1, 'science', 'sir waqar', '01', '07:30:00', '08:30:00'),
            (4, 3, 2, 11, 1, 'Tuesday', 9, 2, 'ict', 'anum ikhlas', '2', '08:30:00', '09:30:00'),
            (7, 4, 2, 3, 2, 'Monday', 8, 1, 'science', 'sir waqar', '01', '07:30:00', '08:30:00'),
            (7, 3, 2, 11, 1, 'Wednesday', 10, 3, 'ict', 'anum ikhlas', '3', '09:30:00', '10:30:00'),
        ]

        for data in test_data:
            cur.execute("""
                INSERT INTO student_timetable_reports
                (StudentID, SemesterID, ProgramID, CourseID, FacultyID, DayOfWeek, SlotID, RoomID, CourseName, FacultyName, RoomNumber, StartTime, EndTime)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, data)

        mysql.connection.commit()
        cur.close()
        print("Test data populated successfully!")

if __name__ == '__main__':
    populate_test_data()
