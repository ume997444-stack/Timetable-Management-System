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

def debug_joins():
    with app.app_context():
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Check assign_courses_to_student
        print("=== assign_courses_to_student ===")
        cur.execute("SELECT * FROM assign_courses_to_student")
        assigns = cur.fetchall()
        for assign in assigns:
            print(assign)

        print("\n=== current_semester ===")
        cur.execute("SELECT * FROM current_semester")
        semesters = cur.fetchall()
        for sem in semesters:
            print(sem)

        print("\n=== schedule ===")
        cur.execute("SELECT * FROM schedule")
        schedules = cur.fetchall()
        for sch in schedules:
            print(sch)

        # Test the JOIN step by step
        print("\n=== Testing JOIN: assign_courses_to_student + current_semester ===")
        cur.execute("""
            SELECT acs.*, cs.SemesterID
            FROM assign_courses_to_student acs
            JOIN current_semester cs ON acs.CurrentSemesterID = cs.CurrentSemesterID
        """)
        step1 = cur.fetchall()
        for row in step1:
            print(row)

        print("\n=== Testing JOIN: with schedule ===")
        cur.execute("""
            SELECT acs.StudentID, cs.SemesterID, acs.ProgramID, acs.CourseID, sch.ScheduleID
            FROM assign_courses_to_student acs
            JOIN current_semester cs ON acs.CurrentSemesterID = cs.CurrentSemesterID
            LEFT JOIN schedule sch ON sch.ProgramID = acs.ProgramID AND sch.SemesterID = cs.SemesterID AND sch.CourseID = acs.CourseID
        """)
        step2 = cur.fetchall()
        for row in step2:
            print(row)

        cur.close()

if __name__ == '__main__':
    debug_joins()
