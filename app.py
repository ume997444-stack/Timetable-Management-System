from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response, abort
from flask_mysqldb import MySQL
import MySQLdb.cursors
from functools import wraps

# Role-based access decorator
def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('loggedin'):
                return redirect(url_for('login'))
            if session.get('role') not in roles:
                flash('Access denied. You do not have permission to view this page.', 'danger')
                # Redirect to role-appropriate home page
                if session.get('role') == 'student':
                    return redirect(url_for('student_timetable'))
                elif session.get('role') == 'teacher':
                    return redirect(url_for('faculty_timetable'))
                else:
                    return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your-very-secret-key'  # Add this line for session/flash support

# List of 30 distinct colors for rooms
ROOM_COLORS = [
    '#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF', '#800000', '#008000', '#000080',
    '#808000', '#800080', '#008080', '#FFA500', '#A52A2A', '#DC143C', '#FF1493', '#FF6347', '#FFD700',
    '#ADFF2F', '#32CD32', '#00CED1', '#1E90FF', '#9370DB', '#FF69B4', '#DDA0DD', '#98FB98', '#F0E68C',
    '#FFA07A', '#20B2AA', '#87CEEB'
]

# Configure MySQL connection (XAMPP settings)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'  # Default MySQL username in XAMPP
app.config['MYSQL_PASSWORD'] = ''  # Default password for MySQL in XAMPP
app.config['MYSQL_DB'] = 'timetable_system'  # Database name

# Initialize MySQL
mysql = MySQL(app)



# Remove global before_request access control.



# Home route - Redirect to login
@app.route('/')
def home():
    return redirect(url_for('login'))

# Route for the index page
@app.route('/index')
def index():
    return redirect(url_for('login'))  # Redirect to the login page

# Route for the dashboard
@app.route('/dashboard')
@role_required('admin')
def dashboard():
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) FROM offered_programs")
    total_offered_programs = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM rooms")
    total_rooms = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM sessions")
    total_sessions = cur.fetchone()[0]

    cur.close()
    return render_template('dashboard.html', total_offered_programs=total_offered_programs, total_rooms=total_rooms, total_sessions=total_sessions)

# -------------------- Departments --------------------

# ---------------- DEPARTMENTS CRUD ---------------- #

# Route to list departments
@app.route('/departments')
def list_departments():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM departments")
    departments = cur.fetchall()
    cur.close()
    return render_template('departments/list_departments.html', departments=departments)

# Route to add a new department
@app.route('/departments/add', methods=['GET', 'POST'])
def add_department():
    if request.method == 'POST':
        department_name = request.form['DepartmentName']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO departments (DepartmentName) VALUES (%s)", (department_name,))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_departments'))
    return render_template('departments/add_department.html')

# Route to update a department
@app.route('/departments/update/<int:id>', methods=['GET', 'POST'])
def update_department(id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM departments WHERE DepartmentID = %s", (id,))
    department = cur.fetchone()
    cur.close()
    if request.method == 'POST':
        department_name = request.form['DepartmentName']
        cur = mysql.connection.cursor()
        cur.execute("UPDATE departments SET DepartmentName = %s WHERE DepartmentID = %s", (department_name, id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_departments'))
    return render_template('departments/update_department.html', department=department)

# Route to delete a department
@app.route('/departments/delete/<int:id>', methods=['POST'])
def delete_department(id):
    try:
        cur = mysql.connection.cursor()
        # Delete all related records in correct order to maintain referential integrity

        # Delete related enrolled students (if any) via courses and students
        cur.execute("""
            DELETE es FROM enrolledstudents es
            JOIN courses c ON es.CourseID = c.CourseID
            WHERE c.DepartmentID = %s
        """, (id,))
        cur.execute("""
            DELETE es FROM enrolledstudents es
            JOIN students s ON es.StudentID = s.StudentID
            WHERE s.DepartmentID = %s
        """, (id,))

        # Delete related attendance records via students and courses
        cur.execute("""
            DELETE a FROM attendance a
            JOIN students s ON a.StudentID = s.StudentID
            WHERE s.DepartmentID = %s
        """, (id,))
        cur.execute("""
            DELETE a FROM attendance a
            JOIN courses c ON a.CourseID = c.CourseID
            WHERE c.DepartmentID = %s
        """, (id,))

        # Delete related timetables via courses
        cur.execute("""
            DELETE t FROM timetables t
            JOIN courses c ON t.CourseID = c.CourseID
            WHERE c.DepartmentID = %s
        """, (id,))

        # Delete related offered_courses via department
        cur.execute("DELETE FROM offered_courses WHERE DepartmentID = %s", (id,))

        # Delete related offered_programs
        cur.execute("DELETE FROM offered_programs WHERE DepartmentID = %s", (id,))

        # Delete related faculty, courses, students
        cur.execute("DELETE FROM faculty WHERE DepartmentID = %s", (id,))
        cur.execute("DELETE FROM courses WHERE DepartmentID = %s", (id,))
        cur.execute("DELETE FROM students WHERE DepartmentID = %s", (id,))

        # Now delete the department
        cur.execute("DELETE FROM departments WHERE DepartmentID = %s", (id,))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_departments'))
    except Exception as e:
        print(f"Error deleting department: {e}")
        return "An error occurred while deleting the department.", 500


# -------------------- Faculty --------------------

# Route to list faculty
@app.route('/faculty')
def list_faculty():
    cur = mysql.connection.cursor()
    cur.execute("SELECT f.FacultyID, f.FirstName, f.LastName, f.Email, d.DepartmentName FROM faculty f LEFT JOIN departments d ON f.DepartmentID = d.DepartmentID")
    faculty_members = cur.fetchall()
    cur.close()
    return render_template('faculty/list_faculty.html', faculty_members=faculty_members)

# Route to add a new faculty
@app.route('/faculty/add', methods=['GET', 'POST'])
def add_faculty():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM departments")
    departments = cur.fetchall()
    cur.close()
    import random, string
    if request.method == 'POST':
        first_name = request.form['FirstName']
        last_name = request.form['LastName']
        email = request.form['Email']
        # Auto-generate password
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        department_id = request.form['DepartmentID']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO faculty (FirstName, LastName, Email, password, DepartmentID) VALUES (%s, %s, %s, %s, %s)", (first_name, last_name, email, password, department_id))
        mysql.connection.commit()
        cur.close()
        flash(f"Faculty added. Auto-generated password: {password}", "success")
        return redirect(url_for('list_faculty'))
    return render_template('faculty/add_faculty.html', departments=departments)

# Route to update a faculty
@app.route('/faculty/update/<int:id>', methods=['GET', 'POST'])
def update_faculty(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM faculty WHERE FacultyID = %s", (id,))
    faculty = cur.fetchone()
    cur.execute("SELECT * FROM departments")
    departments = cur.fetchall()
    cur.close()
    if request.method == 'POST':
        first_name = request.form['FirstName']
        last_name = request.form['LastName']
        email = request.form['Email']
        password = request.form['password']
        department_id = request.form['DepartmentID']
        cur = mysql.connection.cursor()
        cur.execute("UPDATE faculty SET FirstName = %s, LastName = %s, Email = %s, password = %s, DepartmentID = %s WHERE FacultyID = %s", (first_name, last_name, email, password, department_id, id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_faculty'))
    return render_template('faculty/update_faculty.html', faculty=faculty, departments=departments)

# Route to delete a faculty
@app.route('/faculty/delete/<int:id>', methods=['POST'])
def delete_faculty(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM faculty WHERE FacultyID = %s", (id,))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_faculty'))
    except Exception as e:
        print(f"Error deleting faculty: {e}")
        return "An error occurred while deleting the faculty.", 500

# -------------------- Courses --------------------

# Route to list courses
# ---------------- COURSES CRUD ---------------- #

# Route to list courses
@app.route('/courses')
def list_courses():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)  # Use DictCursor
    cur.execute("SELECT c.CourseID, c.CourseName, d.DepartmentName, f.FirstName, f.LastName FROM courses c LEFT JOIN departments d ON c.DepartmentID = d.DepartmentID LEFT JOIN faculty f ON c.FacultyID = f.FacultyID")
    courses = cur.fetchall()
    cur.close()
    return render_template('courses/list_courses.html', courses=courses)

# Route to add a new course
@app.route('/courses/add', methods=['GET', 'POST'])
def add_course():
    if request.method == 'POST':
        try:
            course_name = request.form['CourseName']
            department_id = request.form['DepartmentID']
            faculty_id = request.form['FacultyID']
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO courses (CourseName, DepartmentID, FacultyID) VALUES (%s, %s, %s)", (course_name, department_id, faculty_id))
            mysql.connection.commit()
            cur.close()
            return redirect(url_for('list_courses'))  # Redirect to the course list after adding
        except Exception as e:
            print(f"Error adding course: {e}")
            return "An error occurred while adding the course.", 500

    # Fetch updated list of departments and faculty
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)  # Use DictCursor
    cur.execute("SELECT DepartmentID, DepartmentName FROM departments")
    departments = cur.fetchall()
    cur.execute("SELECT FacultyID, FirstName, LastName FROM faculty")
    faculty = cur.fetchall()
    cur.close()
    return render_template('courses/add_course.html', departments=departments, faculty=faculty)

# Route to update a course
@app.route('/courses/update/<int:id>', methods=['GET', 'POST'])
def update_course(id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)  # Use DictCursor
    cur.execute("SELECT * FROM courses WHERE CourseID = %s", (id,))
    course = cur.fetchone()
    cur.execute("SELECT DepartmentID, DepartmentName FROM departments")
    departments = cur.fetchall()
    cur.execute("SELECT FacultyID, FirstName, LastName FROM faculty")
    faculty = cur.fetchall()
    cur.close()
    if request.method == 'POST':
        course_name = request.form['CourseName']
        department_id = request.form['DepartmentID']
        faculty_id = request.form['FacultyID']
        cur = mysql.connection.cursor()
        cur.execute("UPDATE courses SET CourseName = %s, DepartmentID = %s, FacultyID = %s WHERE CourseID = %s", (course_name, department_id, faculty_id, id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_courses'))
    return render_template('courses/update_course.html', course=course, departments=departments, faculty=faculty)

# Route to delete a course
@app.route('/courses/delete/<int:id>', methods=['POST'])
def delete_course(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM courses WHERE CourseID = %s", (id,))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_courses'))
    except Exception as e:
        print(f"Error deleting course: {e}")
        return "An error occurred while deleting the course.", 500

# -------------------- Students --------------------

# Route to list students
@app.route('/students')
def list_students():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)  # Use DictCursor
    cur.execute("SELECT s.StudentID, s.FirstName, s.LastName, s.EnrollmentNo, s.Email, d.DepartmentName FROM students s LEFT JOIN departments d ON s.DepartmentID = d.DepartmentID")
    students = cur.fetchall()
    cur.close()
    return render_template('students/list_students.html', students=students)

# Route to add a new student
@app.route('/students/add', methods=['GET', 'POST'])
def add_student():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM departments")
    departments = cur.fetchall()
    cur.close()
    import random, string
    if request.method == 'POST':
        first_name = request.form['FirstName']
        last_name = request.form['LastName']
        enrollment_no = request.form['EnrollmentNo']
        email = request.form['Email']
        # Auto-generate password
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        department_id = request.form['DepartmentID']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO students (FirstName, LastName, EnrollmentNo, Email, password, DepartmentID) VALUES (%s, %s, %s, %s, %s, %s)", (first_name, last_name, enrollment_no, email, password, department_id))
        mysql.connection.commit()
        cur.close()
        flash(f"Student added. Auto-generated password: {password}", "success")
        return redirect(url_for('list_students'))  # Redirect to the student list after adding
    return render_template('students/add_student.html', departments=departments)

# Route to update a student
@app.route('/students/update/<int:id>', methods=['GET', 'POST'])
def update_student(id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM students WHERE StudentID = %s", (id,))
    student = cur.fetchone()
    cur.execute("SELECT * FROM departments")
    departments = cur.fetchall()
    cur.close()
    if request.method == 'POST':
        first_name = request.form['FirstName']
        last_name = request.form['LastName']
        enrollment_no = request.form['EnrollmentNo']
        email = request.form['Email']
        password = request.form['password']
        department_id = request.form['DepartmentID']
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE students
            SET FirstName = %s, LastName = %s, EnrollmentNo = %s, Email = %s, password = %s, DepartmentID = %s
            WHERE StudentID = %s
        """, (first_name, last_name, enrollment_no, email, password, department_id, id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_students'))
    return render_template('students/update_student.html', student=student, departments=departments)

# Route to delete a student
@app.route('/students/delete/<int:id>', methods=['POST'])
def delete_student(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM students WHERE StudentID = %s", (id,))  # Corrected column name
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_students'))
    except Exception as e:
        print(f"Error deleting student: {e}")
        return "An error occurred while deleting the student.", 500

# -------------------- Attendance --------------------

# Route to list attendance records
@app.route('/attendance')
def list_attendance():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT a.AttendanceID, s.FirstName, s.LastName, c.CourseName, a.AttendanceDate, a.AttendanceStatus
        FROM attendance a
        LEFT JOIN students s ON a.StudentID = s.StudentID
        LEFT JOIN courses c ON a.CourseID = c.CourseID
    """)  # Updated to use CourseID
    attendance_records = cur.fetchall()
    cur.close()
    return render_template('attendance/list_attendance.html', attendance_records=attendance_records)

# Route to add a new attendance record
@app.route('/attendance/add', methods=['GET', 'POST'])
def add_attendance():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM students")
    students = cur.fetchall()
    cur.execute("SELECT * FROM courses")  # Ensure this query fetches the correct column names
    courses = cur.fetchall()
    cur.close()
    if request.method == 'POST':
        student_id = request.form['StudentID']
        course_id = request.form['CourseID']  # Updated to 'CourseID'
        attendance_date = request.form['AttendanceDate']
        attendance_status = 'Present' if 'AttendanceStatus' in request.form else 'Absent'
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO attendance (StudentID, CourseID, AttendanceDate, AttendanceStatus) VALUES (%s, %s, %s, %s)", (student_id, course_id, attendance_date, attendance_status))  # Updated query
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_attendance'))  # Redirect to the attendance list after adding
    return render_template('attendance/add_attendance.html', students=students, courses=courses)

# Route to update an attendance record
@app.route('/attendance/update/<int:id>', methods=['GET', 'POST'])
def update_attendance(id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM attendance WHERE AttendanceID = %s", (id,))
    attendance = cur.fetchone()
    cur.execute("SELECT * FROM students")
    students = cur.fetchall()
    cur.execute("SELECT * FROM courses")  # Ensure this query fetches the correct column names
    courses = cur.fetchall()
    cur.close()
    if request.method == 'POST':
        student_id = request.form['StudentID']
        course_id = request.form['CourseID']  # Updated to 'CourseID'
        attendance_date = request.form['AttendanceDate']
        attendance_status = 'Present' if 'AttendanceStatus' in request.form else 'Absent'
        cur = mysql.connection.cursor()
        cur.execute("UPDATE attendance SET StudentID = %s, CourseID = %s, AttendanceDate = %s, AttendanceStatus = %s WHERE AttendanceID = %s", (student_id, course_id, attendance_date, attendance_status, id))  # Updated query
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_attendance'))
    return render_template('attendance/update_attendance.html', attendance=attendance, students=students, courses=courses)

# Route to delete an attendance record
@app.route('/attendance/delete/<int:id>', methods=['POST'])
def delete_attendance(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM attendance WHERE AttendanceID = %s", (id,))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_attendance'))
    except Exception as e:
        print(f"Error deleting attendance record: {e}")
        return "An error occurred while deleting the attendance record.", 500

# -------------------- Timetables --------------------

# Route to list timetables
@app.route('/timetables')
def list_timetables():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT t.TimetableID, c.CourseName, t.DayOfWeek, t.StartTime, t.EndTime, t.RoomNumber FROM timetables t LEFT JOIN courses c ON t.CourseID = c.CourseID")
    timetables = cur.fetchall()
    cur.close()
    return render_template('timetables/list_timetables.html', timetables=timetables)

# Route to add a new timetable
@app.route('/timetables/add', methods=['GET', 'POST'])
def add_timetable():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    semester_id = request.form.get('SemesterID')
    
    # Fetch existing classes for the selected semester
    cur.execute("""
        SELECT CourseID FROM schedule WHERE SemesterID = %s
    """, (semester_id,))
    scheduled_courses = {row['CourseID'] for row in cur.fetchall()}

    # Fetch all courses
    cur.execute("SELECT * FROM courses")
    all_courses = cur.fetchall()

    # Filter out the scheduled ones
    cur.execute("SELECT * FROM courses")
    courses = [course for course in cur.fetchall() if course['CourseID'] not in scheduled_courses]
    cur.execute("SELECT FacultyID, CONCAT(FirstName, ' ', LastName) AS FullName FROM faculty")  # Fetch faculty names
    faculty = cur.fetchall()
    cur.close()
    if request.method == 'POST':
        course_id = request.form['CourseID']
        day_of_week = request.form['DayOfWeek']
        start_time = request.form['StartTime']
        end_time = request.form['EndTime']
        room_number = request.form['RoomNumber']
        taught_by = request.form['TaughtBy']  # Foreign key (FacultyID)

        # Validate overlapping time slots for the teacher and the classroom
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            SELECT t.*
            FROM timetables t
            WHERE t.DayOfWeek = %s
            AND (
                (t.StartTime < t.EndTime AND (%s < t.EndTime AND %s > t.StartTime)) OR
                (t.StartTime > t.EndTime AND (%s < t.EndTime OR %s > t.StartTime))  -- Handle crossing midnight
            )
            AND (t.RoomNumber = %s OR t.TaughtBy = %s)
        """, (day_of_week, end_time, start_time, end_time, start_time, room_number, taught_by))
        conflict = cur.fetchone()
        cur.close()

        if conflict:
            return "Error: Time slot conflicts with an existing timetable entry for the same teacher or classroom.", 400

        # Insert new timetable entry
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO timetables (CourseID, DayOfWeek, StartTime, EndTime, RoomNumber, TaughtBy)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (course_id, day_of_week, start_time, end_time, room_number, taught_by))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_timetables'))
    return render_template('timetables/add_timetable.html', courses=courses, faculty=faculty)

# Route to update a timetable
@app.route('/timetables/update/<int:id>', methods=['GET', 'POST'])
def update_timetable(id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM timetables WHERE TimetableID = %s", (id,))
    timetable = cur.fetchone()
    cur.execute("SELECT * FROM courses")
    courses = cur.fetchall()
    cur.execute("SELECT FacultyID, CONCAT(FirstName, ' ', LastName) AS FullName FROM faculty")  # Fetch faculty names
    faculty = cur.fetchall()
    cur.close()
    if request.method == 'POST':
        course_id = request.form['CourseID']
        day_of_week = request.form['DayOfWeek']
        start_time = request.form['StartTime']
        end_time = request.form['EndTime']
        room_number = request.form['RoomNumber']
        taught_by = request.form['TaughtBy']  # Foreign key (FacultyID)

        # Validate overlapping time slots for the teacher and the classroom
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            SELECT t.*
            FROM timetables t
            WHERE t.DayOfWeek = %s
            AND (
                (t.StartTime < t.EndTime AND (%s < t.EndTime AND %s > t.StartTime)) OR
                (t.StartTime > t.EndTime AND (%s < t.EndTime OR %s > t.StartTime))  -- Handle crossing midnight
            )
            AND (t.RoomNumber = %s OR t.TaughtBy = %s)
            AND t.TimetableID != %s
        """, (day_of_week, end_time, start_time, end_time, start_time, room_number, taught_by, id))
        conflict = cur.fetchone()
        cur.close()

        if conflict:
            return "Error: Time slot conflicts with an existing timetable entry for the same teacher or classroom.", 400

        # Update timetable entry
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE timetables
            SET CourseID = %s, DayOfWeek = %s, StartTime = %s, EndTime = %s, RoomNumber = %s, TaughtBy = %s
            WHERE TimetableID = %s
        """, (course_id, day_of_week, start_time, end_time, room_number, taught_by, id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_timetables'))
    return render_template('timetables/update_timetable.html', timetable=timetable, courses=courses, faculty=faculty)

# Route to delete a timetable
@app.route('/timetables/delete/<int:id>', methods=['POST'])
def delete_timetable(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM timetables WHERE TimetableID = %s", (id,))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_timetables'))
    except Exception as e:
        print(f"Error deleting timetable: {e}")
        return "An error occurred while deleting the timetable.", 500

# -------------------- Enrolled Students --------------------

# Route to list enrolled students
@app.route('/enrolled_students')
def list_enrolled_students():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT es.EnrollmentID, s.FirstName, s.LastName, c.CourseName
        FROM enrolledstudents es
        JOIN students s ON es.StudentID = s.StudentID
        JOIN courses c ON es.CourseID = c.CourseID
    """)  # Corrected column names
    enrolled_students = cur.fetchall()
    cur.close()
    return render_template('enrolled_students/list_enrolled_students.html', enrolled_students=enrolled_students)

# Route to add a new enrolled student
@app.route('/enrolled_students/add', methods=['GET', 'POST'])
def add_enrolled_student():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM students")
    students = cur.fetchall()
    cur.execute("SELECT * FROM courses")
    courses = cur.fetchall()
    cur.execute("SELECT * FROM semesters")  # Added semesters for SemesterID
    semesters = cur.fetchall()
    cur.close()
    if request.method == 'POST':
        student_id = request.form['StudentID']
        course_id = request.form['CourseID']
        semester_id = request.form['SemesterID']  # Added SemesterID
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO enrolledstudents (StudentID, CourseID, SemesterID) VALUES (%s, %s, %s)", (student_id, course_id, semester_id))  # Corrected query
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_enrolled_students'))
    return render_template('enrolled_students/add_enrolled_student.html', students=students, courses=courses, semesters=semesters)

# Route to delete an enrolled student
@app.route('/enrolled_students/delete/<int:id>', methods=['POST'])
def delete_enrolled_student(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM enrolledstudents WHERE EnrollmentID = %s", (id,))  # Corrected column name
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_enrolled_students'))
    except Exception as e:
        print(f"Error deleting enrolled student: {e}")
        return "An error occurred while deleting the enrolled student.", 500

# -------------------- Enrolled Teachers --------------------

# Route to list enrolled teachers


# Route to add offered teacher
@app.route('/offered_teachers/add', methods=['GET', 'POST'])
def add_offered_teacher():
    if request.method == 'POST':
        faculty_id = request.form['FacultyID']
        offered_course_id = request.form['OfferedCourseID']
        # Get DepartmentID and ProgramID from offered_course
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT oc.ProgramID, p.DepartmentID FROM offered_courses oc JOIN programs p ON oc.ProgramID = p.ProgramID WHERE oc.OfferedCourseID = %s", (offered_course_id,))
        course_info = cur.fetchone()
        cur.close()
        if course_info:
            program_id = course_info['ProgramID']
            department_id = course_info['DepartmentID']
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO offered_teachers (FacultyID, OfferedCourseID, DepartmentID, ProgramID) VALUES (%s, %s, %s, %s)",
                        (faculty_id, offered_course_id, department_id, program_id))
            mysql.connection.commit()
            cur.close()
            return redirect(url_for('list_offered_teachers'))
        else:
            flash("Invalid Offered Course ID", "danger")
            return redirect(url_for('add_offered_teacher'))
    # Fetch faculty and offered_courses for dropdowns
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT FacultyID, FirstName, LastName FROM faculty")
    faculty = cur.fetchall()
    cur.execute("""
        SELECT oc.OfferedCourseID, c.CourseName, s.SemesterName
        FROM offered_courses oc
        JOIN courses c ON oc.CourseID = c.CourseID
        JOIN semesters s ON oc.SemesterID = s.SemesterID
    """)
    offered_courses = cur.fetchall()
    cur.close()
    return render_template('offered_teachers/add_offered_teacher.html', faculty=faculty, offered_courses=offered_courses)

# -------------------- Offered Courses --------------------

# Route to list offered courses
@app.route('/offered_courses')
def list_offered_courses():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT c.CourseID, c.CourseName, d.DepartmentName, f.FirstName, f.LastName
        FROM courses c
        JOIN departments d ON c.DepartmentID = d.DepartmentID
        JOIN faculty f ON c.FacultyID = f.FacultyID
    """)  # Corrected query
    offered_courses = cur.fetchall()
    cur.close()
    return render_template('offered_courses/list_offered_courses.html', offered_courses=offered_courses)

# Route to add a new offered course
@app.route('/offered_courses/add', methods=['GET', 'POST'])
def add_offered_course():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM courses")
    courses = cur.fetchall()
    cur.execute("SELECT * FROM semesters")
    semesters = cur.fetchall()
    cur.execute("SELECT * FROM departments")
    departments = cur.fetchall()
    cur.close()
    if request.method == 'POST':
        course_id = request.form['CourseID']
        semester_id = request.form['SemesterID']
        department_id = request.form['DepartmentID']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO offered_courses (CourseID, SemesterID, DepartmentID) VALUES (%s, %s, %s)", (course_id, semester_id, department_id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_offered_courses'))
    return render_template('offered_courses/add_offered_course.html', courses=courses, semesters=semesters, departments=departments)

# Route to delete an offered course
@app.route('/offered_courses/delete/<int:id>', methods=['POST'])
def delete_offered_course(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM offered_courses WHERE OfferedCourseID = %s", (id,))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_offered_courses'))
    except Exception as e:
        print(f"Error deleting offered course: {e}")
        return "An error occurred while deleting the offered course.", 500

# -------------------- Semesters --------------------

# Route to list semesters
@app.route('/semesters')
def list_semesters():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM semesters")
    semesters = cur.fetchall()
    cur.close()
    return render_template('semesters/list_semesters.html', semesters=semesters)

# Route to add a new semester
@app.route('/semesters/add', methods=['GET', 'POST'])
def add_semester():
    if request.method == 'POST':
        semester_name = request.form['SemesterName']
        email = request.form['Email']
        password = request.form['Password']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO semesters (SemesterName, Email, Password) VALUES (%s, %s, %s)", (semester_name, email, password))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_semesters'))
    return render_template('semesters/add_semester.html')

# Route to update a semester
@app.route('/semesters/update/<int:id>', methods=['GET', 'POST'])
def update_semester(id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM semesters WHERE SemesterID = %s", (id,))
    semester = cur.fetchone()
    cur.close()
    if request.method == 'POST':
        semester_name = request.form['SemesterName']
        email = request.form['Email']
        password = request.form['Password']
        cur = mysql.connection.cursor()
        cur.execute("UPDATE semesters SET SemesterName = %s, Email = %s, Password = %s WHERE SemesterID = %s", (semester_name, email, password, id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_semesters'))
    return render_template('semesters/update_semester.html', semester=semester)

# Route to delete a semester
@app.route('/semesters/delete/<int:id>', methods=['POST'])
def delete_semester(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM semesters WHERE SemesterID = %s", (id,))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_semesters'))
    except Exception as e:
        print(f"Error deleting semester: {e}")
        return "An error occurred while deleting the semester.", 500

# -------------------- Sessions --------------------

# Route to list sessions

# Route to list sessions
@app.route('/sessions')
def list_sessions():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM sessions")
    sessions = cur.fetchall()
    cur.close()
    return render_template('sessions/list_sessions.html', sessions=sessions)

# Route to add a new session
@app.route('/sessions/add', methods=['GET', 'POST'])
def add_session():
    if request.method == 'POST':
        start_year = request.form['StartYear']
        end_year = request.form['EndYear']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO sessions (StartYear, EndYear) VALUES (%s, %s)", (start_year, end_year))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_sessions'))
    return render_template('sessions/add_session.html')

# Route to update a session
@app.route('/sessions/update/<int:id>', methods=['GET', 'POST'])
def update_session(id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM sessions WHERE SessionID = %s", (id,))
    session = cur.fetchone()
    cur.close()
    if request.method == 'POST':
        start_year = request.form['StartYear']
        end_year = request.form['EndYear']
        cur = mysql.connection.cursor()
        cur.execute("UPDATE sessions SET StartYear = %s, EndYear = %s WHERE SessionID = %s", (start_year, end_year, id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_sessions'))
    return render_template('sessions/update_session.html', session=session)

# Route to delete a session
@app.route('/sessions/delete/<int:id>', methods=['POST'])
def delete_session(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM sessions WHERE SessionID = %s", (id,))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_sessions'))
    except Exception as e:
        print(f"Error deleting session: {e}")
        return "An error occurred while deleting the session.", 500

# -------------------- Offered Programs --------------------

# Route to list offered programs
# ---------------- PROGRAMS CRUD ---------------- #

# Route to list offered programs
@app.route('/offered_programs')
def list_offered_programs():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT op.ProgramID, op.ProgramName, s.StartYear, s.EndYear, d.DepartmentName
        FROM offered_programs op
        JOIN sessions s ON op.SessionID = s.SessionID
        LEFT JOIN departments d ON op.DepartmentID = d.DepartmentID
    """)
    programs = cur.fetchall()
    cur.close()
    return render_template('offered_programs/list_offered_programs.html', programs=programs)

# Route to add a new offered program
@app.route('/offered_programs/add', methods=['GET', 'POST'])
def add_offered_program():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM sessions")
    sessions = cur.fetchall()
    cur.execute("SELECT * FROM departments")
    departments = cur.fetchall()
    cur.close()
    if request.method == 'POST':
        program_id = request.form['ProgramID']
        program_name = request.form['ProgramName']
        session_id = request.form['SessionID']
        department_id = request.form['DepartmentID']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO offered_programs (ProgramID, ProgramName, SessionID, DepartmentID) VALUES (%s, %s, %s, %s)", (program_id, program_name, session_id, department_id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_offered_programs'))
    return render_template('offered_programs/add_offered_program.html', sessions=sessions, departments=departments)

# Route to update an offered program
@app.route('/offered_programs/update/<int:id>', methods=['GET', 'POST'])
def update_offered_program(id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM offered_programs WHERE ProgramID = %s", (id,))
    program = cur.fetchone()
    cur.execute("SELECT * FROM sessions")
    sessions = cur.fetchall()
    cur.execute("SELECT * FROM departments")
    departments = cur.fetchall()
    cur.close()
    if request.method == 'POST':
        program_name = request.form['ProgramName']
        session_id = request.form['SessionID']
        department_id = request.form['DepartmentID']
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE offered_programs
            SET ProgramName = %s, SessionID = %s, DepartmentID = %s
            WHERE ProgramID = %s
        """, (program_name, session_id, department_id, id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_offered_programs'))
    return render_template('offered_programs/update_offered_program.html', program=program, sessions=sessions, departments=departments)

# Route to delete an offered program
@app.route('/offered_programs/delete/<int:id>', methods=['POST'])
def delete_offered_program(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM offered_programs WHERE ProgramID = %s", (id,))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_offered_programs'))
    except Exception as e:
        print(f"Error deleting offered program: {e}")
        return "An error occurred while deleting the offered program.", 500


# -------------------- Current Semester --------------------

# Route to list current semesters
@app.route('/current_semester')
def list_current_semester():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT cs.CurrentSemesterID, op.ProgramName, s.SemesterName, cs.StartDate, cs.EndDate
        FROM current_semester cs
        JOIN offered_programs op ON cs.ProgramID = op.ProgramID
        JOIN semesters s ON cs.SemesterID = s.SemesterID
    """)  # Fixed SQL query
    current_semesters = cur.fetchall()
    cur.close()
    return render_template('current_semester/list_current_semester.html', current_semesters=current_semesters)

# Route to add a new current semester
@app.route('/current_semester/add', methods=['GET', 'POST'])
def add_current_semester():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT op.*, s.StartYear, s.EndYear FROM offered_programs op JOIN sessions s ON op.SessionID = s.SessionID")
    programs = cur.fetchall()
    cur.execute("SELECT * FROM semesters")
    semesters = cur.fetchall()
    cur.close()
    if request.method == 'POST':
        program_id = request.form['ProgramID']
        semester_id = request.form['SemesterID']
        start_date = request.form['StartDate']
        end_date = request.form['EndDate']
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO current_semester (ProgramID, SemesterID, StartDate, EndDate)
            VALUES (%s, %s, %s, %s)
        """, (program_id, semester_id, start_date, end_date))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_current_semester'))
    return render_template('current_semester/add_current_semester.html', programs=programs, semesters=semesters)

# Route to delete a current semester
@app.route('/current_semester/delete/<int:id>', methods=['POST'])
def delete_current_semester(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM current_semester WHERE CurrentSemesterID = %s", (id,))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_current_semester'))
    except Exception as e:
        print(f"Error deleting current semester: {e}")
        return "An error occurred while deleting the current semester.", 500

# -------------------- Assign Courses to Students --------------------

# Route to list assigned courses to students (grouped by student, program, duration, semester)
@app.route('/assign_courses_to_student')
def list_assign_courses_to_student():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT 
            ac.AssignID,
            s.StudentID, s.FirstName, op.ProgramName, se.StartYear, se.EndYear,
            sem.SemesterName, c.CourseName,
            ac.Allowed, ac.Is_Repeater
        FROM assign_courses_to_student ac
        JOIN students s ON ac.StudentID = s.StudentID
        JOIN offered_programs op ON ac.ProgramID = op.ProgramID
        JOIN sessions se ON ac.SessionID = se.SessionID
        JOIN current_semester cs ON ac.CurrentSemesterID = cs.CurrentSemesterID
        JOIN semesters sem ON cs.SemesterID = sem.SemesterID
        JOIN courses c ON ac.CourseID = c.CourseID
        ORDER BY s.StudentID, sem.SemesterName, c.CourseName
    """)
    rows = cur.fetchall()
    cur.close()

    grouped = {}
    for row in rows:
        key = (
            row['StudentID'],
            row['FirstName'],
            row['ProgramName'],
            f"{row['StartYear']}–{row['EndYear']}",
            row['SemesterName']
        )
        if key not in grouped:
            grouped[key] = []
        grouped[key].append({
            'AssignmentID': row.get('AssignID'),
            'CourseName': row['CourseName'],
            'Allowed': row.get('Allowed'),
            'Is_Repeater': row.get('Is_Repeater')
        })

    return render_template(
        'assign_courses_to_student/list_assign_courses_to_student.html',
        grouped=grouped
    )

# Route to assign a course to a student
@app.route('/assign_courses_to_student/add', methods=['GET', 'POST'])
def add_assign_courses_to_student():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM students")
    students = cur.fetchall()
    cur.execute("SELECT op.ProgramID, op.ProgramName, op.SessionID, s.StartYear, s.EndYear FROM offered_programs op JOIN sessions s ON op.SessionID = s.SessionID")
    programs = cur.fetchall()
    cur.execute("SELECT * FROM courses")
    courses = cur.fetchall()
    cur.close()

    # For GET, show all current semesters (with program/session info for filtering in JS)
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT cs.CurrentSemesterID, cs.ProgramID, cs.SemesterID, op.ProgramName, s.SemesterName
        FROM current_semester cs
        JOIN offered_programs op ON cs.ProgramID = op.ProgramID
        JOIN semesters s ON cs.SemesterID = s.SemesterID
    """)
    current_semesters = cur.fetchall()
    cur.close()

    if request.method == 'POST':
        student_id = request.form['StudentID']
        program_id = request.form['ProgramID']
        # Find session_id for the selected program
        session_id = None
        for p in programs:
            if str(p['ProgramID']) == str(program_id):
                session_id = p['SessionID']
                break
        current_semester_id = request.form['CurrentSemesterID']
        course_id = request.form['CourseID']
        allowed = request.form.get('Allowed', 'Yes')
        is_repeater = request.form.get('Is_Repeater', 'No')
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO assign_courses_to_student
            (StudentID, ProgramID, SessionID, CurrentSemesterID, CourseID, Allowed, Is_Repeater)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (student_id, program_id, session_id, current_semester_id, course_id, allowed, is_repeater))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_assign_courses_to_student'))
    return render_template(
        'assign_courses_to_student/add_assign_courses_to_student.html',
        students=students, programs=programs, current_semesters=current_semesters, courses=courses
    )

# Add an update route for assigned courses
@app.route('/assign_courses_to_student/update/<int:assign_id>', methods=['GET', 'POST'])
def update_assign_courses_to_student(assign_id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM assign_courses_to_student WHERE AssignID = %s", (assign_id,))
    assignment = cur.fetchone()
    cur.execute("SELECT * FROM students")
    students = cur.fetchall()
    cur.execute("SELECT * FROM courses")
    courses = cur.fetchall()
    cur.close()
    if request.method == 'POST':
        allowed = request.form.get('Allowed', 'Yes')
        is_repeater = request.form.get('Is_Repeater', 'No')
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE assign_courses_to_student
            SET Allowed = %s, Is_Repeater = %s
            WHERE AssignID = %s
        """, (allowed, is_repeater, assign_id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_assign_courses_to_student'))
    return render_template(
        'assign_courses_to_student/update_assign_courses_to_student.html',
        assignment=assignment, students=students, courses=courses
    )

# -------------------- Rooms --------------------

@app.route('/rooms')
def list_rooms():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM rooms")
    rooms = cur.fetchall()
    cur.close()
    return render_template('rooms/list_rooms.html', rooms=rooms)

@app.route('/rooms/add', methods=['GET', 'POST'])
def add_room():
    if request.method == 'POST':
        room_number = request.form['RoomNumber']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO rooms (RoomNumber) VALUES (%s)", (room_number,))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_rooms'))
    return render_template('rooms/add_room.html')

@app.route('/rooms/update/<int:id>', methods=['GET', 'POST'])
def update_room(id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM rooms WHERE RoomID = %s", (id,))
    room = cur.fetchone()
    cur.close()
    if request.method == 'POST':
        room_number = request.form['RoomNumber']
        cur = mysql.connection.cursor()
        cur.execute("UPDATE rooms SET RoomNumber = %s WHERE RoomID = %s", (room_number, id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_rooms'))
    return render_template('rooms/update_room.html', room=room)

@app.route('/rooms/delete/<int:id>', methods=['POST'])
def delete_room(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM rooms WHERE RoomID = %s", (id,))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_rooms'))
    except Exception as e:
        print(f"Error deleting room: {e}")
        return "An error occurred while deleting the room.", 500

# -------------------- Timetable Views and Management --------------------

# View timetable for a given day (default: Monday)
@app.route('/timetable', methods=['GET', 'POST'])
def view_timetable():
    day = request.args.get('day', 'Monday')
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM rooms")
    rooms = cur.fetchall()
    cur.execute("SELECT * FROM time_slots ORDER BY StartTime")
    slots = cur.fetchall()
    # Fetch all scheduled classes for the day
    cur.execute("""
        SELECT s.*, r.RoomNumber, f.FirstName, f.LastName, c.CourseName, ts.StartTime, ts.EndTime, op.ProgramName
        FROM schedule s
        JOIN rooms r ON s.RoomID = r.RoomID
        JOIN faculty f ON s.FacultyID = f.FacultyID
        JOIN courses c ON s.CourseID = c.CourseID
        JOIN time_slots ts ON s.SlotID = ts.SlotID
        LEFT JOIN offered_programs op ON s.ProgramID = op.ProgramID
        WHERE s.DayOfWeek = %s
    """, (day,))
    scheduled = cur.fetchall()
    cur.close()
    # Build a lookup: {(room_id, slot_id): class_info}
    scheduled_lookup = {(s['RoomID'], s['SlotID']): s for s in scheduled}
    return render_template('timetable/view_timetable.html', rooms=rooms, slots=slots, scheduled_lookup=scheduled_lookup, day=day)

# Add a class (with conflict prevention)
@app.route('/timetable/add', methods=['GET', 'POST'])
def add_class():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM sessions")
    sessions = cur.fetchall()
    cur.execute("SELECT * FROM rooms")
    rooms = cur.fetchall()
    cur.execute("SELECT * FROM faculty")
    faculty = cur.fetchall()
    cur.execute("SELECT * FROM courses")
    courses = cur.fetchall()
    cur.execute("SELECT * FROM offered_programs")
    programs = cur.fetchall()
    cur.execute("SELECT * FROM departments")
    departments = cur.fetchall()
    cur.execute("SELECT * FROM time_slots ORDER BY StartTime")
    slots = cur.fetchall()
    # Convert timedelta to HH:MM string
    for slot in slots:
        slot['StartTime'] = f"{slot['StartTime'].seconds // 3600:02d}:{(slot['StartTime'].seconds % 3600) // 60:02d}"
        slot['EndTime'] = f"{slot['EndTime'].seconds // 3600:02d}:{(slot['EndTime'].seconds % 3600) // 60:02d}"
    cur.close()
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

    if request.method == 'POST':
        room_id = request.form['RoomID']
        faculty_id = request.form['FacultyID']
        course_id = request.form['CourseID']
        slot_id = request.form['SlotID']
        day_of_week = request.form['DayOfWeek']
        program_id = request.form.get('ProgramID', None)

        # Validate ProgramID exists
        if not program_id:
            flash("ProgramID is required.", "danger")
            return redirect(url_for('add_class'))

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT ProgramID FROM offered_programs WHERE ProgramID = %s", (program_id,))
        program_exists = cur.fetchone()
        if not program_exists:
            cur.close()
            flash("Invalid ProgramID: does not exist in offered_programs.", "danger")
            return redirect(url_for('add_class'))

        # Conflict check: no overlap in same room, same day, same slot
        cur.execute("""
            SELECT * FROM schedule
            WHERE RoomID = %s AND SlotID = %s AND DayOfWeek = %s
        """, (room_id, slot_id, day_of_week))
        conflict = cur.fetchone()

        if conflict:
            flash("Conflict: Room already booked for this slot and day.", "danger")
            return redirect(url_for('add_class'))

        # Check for faculty conflict
        cur.execute("""
            SELECT * FROM schedule
            WHERE FacultyID = %s AND SlotID = %s AND DayOfWeek = %s
        """, (faculty_id, slot_id, day_of_week))
        faculty_conflict = cur.fetchone()

        if faculty_conflict:
            flash("Conflict: Faculty already booked for this slot and day.", "danger")
            return redirect(url_for('add_class'))

        # Check if subject is already scheduled for this program on the same day
        cur.execute("""
            SELECT c.CourseName, s.* 
            FROM schedule s
            JOIN courses c ON s.CourseID = c.CourseID
            WHERE s.ProgramID = %s AND s.DayOfWeek = %s AND s.CourseID = %s
        """, (program_id, day_of_week, course_id))
        subject_conflict = cur.fetchone()

        if subject_conflict:
            cur.execute("SELECT CourseName FROM courses WHERE CourseID = %s", (course_id,))
            course_info = cur.fetchone()
            course_name = course_info['CourseName'] if course_info else ""
            flash(f"Conflict: {course_name} is already scheduled for this program on {day_of_week}.", "danger")
            cur.close()
            return redirect(url_for('add_class'))

        # Insert class
        cur = mysql.connection.cursor()
        # Assuming default SemesterID as 1, adjust if needed
        cur.execute("""
            INSERT INTO schedule (CourseID, FacultyID, RoomID, SlotID, DayOfWeek, SemesterID, ProgramID)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (course_id, faculty_id, room_id, slot_id, day_of_week, 1, program_id))
        mysql.connection.commit()
        cur.close()
        flash("Class scheduled successfully!", "success")
        return redirect(url_for('room_timetable'))

    return render_template('timetable/add_class.html', rooms=rooms, faculty=faculty, courses=courses, programs=programs, slots=slots, days=days, sessions=sessions, departments=departments)

# Helper: Check for room/faculty conflicts
def has_conflict(room_id, faculty_id, slot_id, day, semester_id, program_id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # Room conflict
    cur.execute("""
        SELECT * FROM schedule
        WHERE RoomID=%s AND SlotID=%s AND DayOfWeek=%s AND SemesterID=%s
    """, (room_id, slot_id, day, semester_id))
    if cur.fetchone():
        cur.close()
        return "Room is already booked for this slot."
    # Faculty conflict (including ProgramID to match unique constraint)
    cur.execute("""
        SELECT * FROM schedule
        WHERE FacultyID=%s AND SlotID=%s AND DayOfWeek=%s AND ProgramID=%s
    """, (faculty_id, slot_id, day, program_id))
    if cur.fetchone():
        cur.close()
        return "Faculty is already booked for this slot in this program."
    cur.close()
    return None

# Add a course to a class (assign slot, room, faculty)
@app.route('/schedule/add', methods=['GET', 'POST'])
def add_schedule():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM programs")
    programs = cur.fetchall()
    cur.execute("SELECT * FROM semesters")
    semesters = cur.fetchall()
    cur.execute("SELECT * FROM courses")
    courses = cur.fetchall()
    cur.execute("SELECT * FROM faculty")
    faculty = cur.fetchall()
    cur.execute("SELECT * FROM rooms")
    rooms = cur.fetchall()
    cur.execute("SELECT * FROM time_slots ORDER BY StartTime")
    slots = cur.fetchall()
    cur.close()
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

    if request.method == 'POST':
        program_id = request.form['ProgramID']
        semester_id = request.form['SemesterID']
        course_id = request.form['CourseID']
        faculty_id = request.form['FacultyID']
        room_id = request.form['RoomID']
        slot_id = request.form['SlotID']
        day = request.form['DayOfWeek']

        # Conflict check
        conflict = has_conflict(room_id, faculty_id, slot_id, day, semester_id)
        if conflict:
            flash(conflict, "danger")
            return redirect(url_for('add_schedule'))

        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO schedule (CourseID, FacultyID, RoomID, SlotID, DayOfWeek, SemesterID, ProgramID)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (course_id, faculty_id, room_id, slot_id, day, semester_id, program_id))
        mysql.connection.commit()
        cur.close()
        flash("Class scheduled successfully!", "success")
        return redirect(url_for('room_timetable'))

    return render_template('schedule/add_schedule.html', programs=programs, semesters=semesters, courses=courses, faculty=faculty, rooms=rooms, slots=slots, days=days)

# Class-wise timetable (filterable)
@app.route('/timetable/room', methods=['GET'])
def room_timetable():
    program_id = request.args.get('program_id', type=int)
    semester_id = request.args.get('semester_id', type=int)
    day = request.args.get('day', 'Monday')
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Get all programs and semesters for filters
    cur.execute("SELECT * FROM offered_programs")
    programs = cur.fetchall()
    cur.execute("SELECT * FROM semesters")
    semesters = cur.fetchall()
    cur.execute("SELECT * FROM time_slots ORDER BY StartTime")
    slots = cur.fetchall()
    cur.execute("SELECT * FROM rooms")
    rooms = cur.fetchall()

    # Fetch scheduled classes with comprehensive filtering
    query = """
        SELECT s.*, c.CourseName, f.FirstName, f.LastName, r.RoomNumber,
               ts.StartTime, ts.EndTime, op.ProgramName, d.DepartmentName, sem.SemesterName
        FROM schedule s
        JOIN courses c ON s.CourseID = c.CourseID
        JOIN faculty f ON s.FacultyID = f.FacultyID
        JOIN rooms r ON s.RoomID = r.RoomID
        JOIN time_slots ts ON s.SlotID = ts.SlotID
        LEFT JOIN offered_programs op ON s.ProgramID = op.ProgramID
        LEFT JOIN departments d ON op.DepartmentID = d.DepartmentID
        LEFT JOIN semesters sem ON s.SemesterID = sem.SemesterID
        WHERE s.DayOfWeek=%s
    """
    params = [day]
    
    if program_id:
        query += " AND s.ProgramID=%s"
        params.append(program_id)
    if semester_id:
        query += " AND s.SemesterID=%s"
        params.append(semester_id)
    
    cur.execute(query, tuple(params))
    scheduled = cur.fetchall()
    
    cur.close()
    
    # Lookup: {(slot_id, room_id): class_info}
    scheduled_lookup = {(s['SlotID'], s['RoomID']): s for s in scheduled}
    
    return render_template('schedule/class_timetable.html',
                         programs=programs, semesters=semesters, 
                         slots=slots, rooms=rooms, 
                         scheduled_lookup=scheduled_lookup, 
                         program_id=program_id, semester_id=semester_id, day=day)

# Faculty-wise timetable
@app.route('/timetable/faculty', methods=['GET'])
def faculty_timetable():
    # Session-based access control
    if not session.get('loggedin'):
        return redirect(url_for('login'))
    if session.get('role') not in ['teacher', 'admin']:
        flash('Access denied. Only teachers and admins can view faculty timetables.', 'danger')
        return redirect(url_for('dashboard'))

    day = request.args.get('day', 'All')
    faculty_id = request.args.get('faculty', 'All')
    if faculty_id == '':
        faculty_id = 'All'

    # For teachers, restrict to their own timetable
    if session.get('role') == 'teacher':
        if faculty_id == 'All':
            faculty_id = str(session['faculty_id'])
        elif faculty_id != 'All' and int(faculty_id) != session.get('faculty_id'):
            flash('You can only view your own timetable.', 'danger')
            return redirect(url_for('faculty_timetable', faculty=session['faculty_id'], day=day))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # Fetch all faculty with their department for dropdown
    cur.execute("""
        SELECT f.FacultyID, f.FirstName, f.LastName, d.DepartmentName
        FROM faculty f
        LEFT JOIN departments d ON f.DepartmentID = d.DepartmentID
        ORDER BY f.FirstName, f.LastName
    """)
    faculties = cur.fetchall()

    # Fetch time slots
    cur.execute("SELECT * FROM time_slots ORDER BY StartTime")
    time_slots = cur.fetchall()

    # Fetch schedules with optional filtering by day and faculty
    query = """
        SELECT s.ScheduleID, s.DayOfWeek, ts.StartTime, ts.EndTime, r.RoomNumber, c.CourseName, f.FacultyID,
               op.ProgramName, sem.SemesterName
        FROM schedule s
        JOIN time_slots ts ON s.SlotID = ts.SlotID
        JOIN rooms r ON s.RoomID = r.RoomID
        JOIN courses c ON s.CourseID = c.CourseID
        JOIN faculty f ON s.FacultyID = f.FacultyID
        LEFT JOIN offered_programs op ON s.ProgramID = op.ProgramID
        LEFT JOIN semesters sem ON s.SemesterID = sem.SemesterID
    """
    params = []
    conditions = []

    if day != 'All':
        conditions.append("s.DayOfWeek = %s")
        params.append(day)

    if faculty_id != 'All':
        conditions.append("f.FacultyID = %s")
        params.append(int(faculty_id))

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY f.FacultyID, s.DayOfWeek, ts.StartTime"
    cur.execute(query, tuple(params))
    schedules = cur.fetchall()
    cur.close()

    # Group schedules by faculty
    faculty_schedules = {}
    for faculty in faculties:
        faculty_schedules[faculty['FacultyID']] = {
            'faculty': faculty,
            'schedules': [s for s in schedules if s['FacultyID'] == faculty['FacultyID']]
        }

    # If filtering by specific faculty, only show that faculty
    if faculty_id != 'All':
        faculty_schedules = {faculty_id: faculty_schedules.get(int(faculty_id), {'faculty': None, 'schedules': []})}

    days = ['All', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

    # Handle case where faculty has no schedule
    for fs in faculty_schedules.values():
        if not fs['schedules']:
            flash(f"No schedule found for faculty {fs['faculty']['FirstName']} {fs['faculty']['LastName']}.", "info")

    return render_template('schedule/faculty_timetable.html', faculty_schedules=faculty_schedules, day=day, days=days, faculties=faculties, faculty=faculty_id, time_slots=time_slots)

# Student-wise timetable
@app.route('/timetable/student', methods=['GET'])
def student_timetable():
    # Session-based access control
    if not session.get('loggedin'):
        return redirect(url_for('login'))
    if session.get('role') not in ['student', 'admin']:
        flash('Access denied. Only students and admins can view student timetables.', 'danger')
        return redirect(url_for('dashboard'))

    program_id = request.args.get('program_id', type=int)
    semester_id = request.args.get('semester_id', type=int)
    day = request.args.get('day', 'All')

    # For students, restrict to their enrolled program and semester
    if session.get('role') == 'student':
        if not program_id or not semester_id:
            # Fetch student's enrollment if not provided
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("SELECT e.SemesterID, op.ProgramID FROM enrolledstudents e JOIN students s ON e.StudentID = s.StudentID JOIN offered_programs op ON op.DepartmentID = s.DepartmentID WHERE e.StudentID = %s LIMIT 1", (session['student_id'],))
            enrollment = cur.fetchone()
            cur.close()
            if enrollment:
                program_id = enrollment['ProgramID']
                semester_id = enrollment['SemesterID']
            else:
                flash('No enrollment found for your account.', 'danger')
                return redirect(url_for('dashboard'))
        else:
            # Verify the provided program_id and semester_id match student's enrollment
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("SELECT e.SemesterID, op.ProgramID FROM enrolledstudents e JOIN students s ON e.StudentID = s.StudentID JOIN offered_programs op ON op.DepartmentID = s.DepartmentID WHERE e.StudentID = %s AND e.SemesterID = %s AND op.ProgramID = %s", (session['student_id'], semester_id, program_id))
            enrollment = cur.fetchone()
            cur.close()
            if not enrollment:
                flash('You can only view timetables for your enrolled program and semester.', 'danger')
                return redirect(url_for('student_timetable'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Fetch all programs and semesters for filters
    cur.execute("SELECT * FROM offered_programs")
    programs = cur.fetchall()
    cur.execute("SELECT * FROM semesters")
    semesters = cur.fetchall()
    cur.execute("SELECT * FROM time_slots ORDER BY StartTime")
    time_slots = cur.fetchall()

    # Fetch student data
    if session.get('role') == 'student':
        cur.execute("SELECT * FROM students WHERE StudentID = %s", (session['student_id'],))
        student = cur.fetchone()
        if student:
            # Add program and semester names if available
            if program_id:
                cur.execute("SELECT ProgramName FROM offered_programs WHERE ProgramID = %s", (program_id,))
                program = cur.fetchone()
                student['ProgramName'] = program['ProgramName'] if program else None
            if semester_id:
                cur.execute("SELECT SemesterName FROM semesters WHERE SemesterID = %s", (semester_id,))
                semester = cur.fetchone()
                student['SemesterName'] = semester['SemesterName'] if semester else None
    else:
        student = None

    # Fetch schedules with optional filtering by program, semester, and day
    query = """
        SELECT s.ScheduleID, s.DayOfWeek, ts.StartTime, ts.EndTime, r.RoomNumber, c.CourseName,
               f.FirstName, f.LastName, op.ProgramName, sem.SemesterName
        FROM schedule s
        JOIN time_slots ts ON s.SlotID = ts.SlotID
        JOIN rooms r ON s.RoomID = r.RoomID
        JOIN courses c ON s.CourseID = c.CourseID
        JOIN faculty f ON s.FacultyID = f.FacultyID
        LEFT JOIN offered_programs op ON s.ProgramID = op.ProgramID
        LEFT JOIN semesters sem ON s.SemesterID = sem.SemesterID
    """
    params = []
    conditions = []

    if program_id:
        conditions.append("s.ProgramID = %s")
        params.append(program_id)
    if semester_id:
        conditions.append("s.SemesterID = %s")
        params.append(semester_id)
    if day != 'All':
        conditions.append("s.DayOfWeek = %s")
        params.append(day)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY s.DayOfWeek, ts.StartTime"
    cur.execute(query, tuple(params))
    schedules = cur.fetchall()
    cur.close()

    return render_template('schedule/student_timetable.html',
                         schedules=schedules, programs=programs, semesters=semesters,
                         time_slots=time_slots, program_id=program_id, semester_id=semester_id, day=day, student=student)

# -------------------- Time Slots --------------------

@app.route('/time_slots')
def list_time_slots():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM time_slots ORDER BY StartTime")
    time_slots = cur.fetchall()
    cur.close()
    return render_template('time_slots/list_time_slots.html', time_slots=time_slots)

@app.route('/time_slots/add', methods=['GET', 'POST'])
def add_time_slot():
    if request.method == 'POST':
        start_time = request.form['StartTime']
        end_time = request.form['EndTime']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO time_slots (StartTime, EndTime) VALUES (%s, %s)", (start_time, end_time))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_time_slots'))
    return render_template('time_slots/add_time_slot.html')

@app.route('/time_slots/update/<int:id>', methods=['GET', 'POST'])
def update_time_slot(id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM time_slots WHERE SlotID = %s", (id,))
    time_slot = cur.fetchone()
    cur.close()
    if request.method == 'POST':
        start_time = request.form['StartTime']
        end_time = request.form['EndTime']
        cur = mysql.connection.cursor()
        cur.execute("UPDATE time_slots SET StartTime = %s, EndTime = %s WHERE SlotID = %s", (start_time, end_time, id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_time_slots'))
    return render_template('time_slots/update_time_slot.html', time_slot=time_slot)

@app.route('/time_slots/delete/<int:id>', methods=['POST'])
def delete_time_slot(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM time_slots WHERE SlotID = %s", (id,))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_time_slots'))
    except Exception as e:
        print(f"Error deleting time slot: {e}")
        return "An error occurred while deleting the time slot.", 500

# -------------------- Professional Faculty-Wise Timetable Report --------------------

@app.route('/faculty_timetable_report', methods=['GET'])
def faculty_timetable_report():
    day = request.args.get('day', 'All')
    faculty_id = request.args.get('faculty', 'All')
    if faculty_id == '':
        faculty_id = 'All'

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # Fetch all faculty with their department for dropdown
    cur.execute("""
        SELECT f.FacultyID, f.FirstName, f.LastName, f.Email, d.DepartmentName
        FROM faculty f
        LEFT JOIN departments d ON f.DepartmentID = d.DepartmentID
        ORDER BY f.FirstName, f.LastName
    """)
    faculties = cur.fetchall()

    # Fetch time slots
    cur.execute("SELECT * FROM time_slots ORDER BY StartTime")
    time_slots = cur.fetchall()

    # Fetch schedules with optional filtering by day and faculty
    query = """
        SELECT s.ScheduleID, s.DayOfWeek, ts.StartTime, ts.EndTime, r.RoomNumber, c.CourseName, f.FacultyID,
               op.ProgramName, sem.SemesterName
        FROM schedule s
        JOIN time_slots ts ON s.SlotID = ts.SlotID
        JOIN rooms r ON s.RoomID = r.RoomID
        JOIN courses c ON s.CourseID = c.CourseID
        JOIN faculty f ON s.FacultyID = f.FacultyID
        LEFT JOIN offered_programs op ON s.ProgramID = op.ProgramID
        LEFT JOIN semesters sem ON s.SemesterID = sem.SemesterID
    """
    params = []
    conditions = []

    if day != 'All':
        conditions.append("s.DayOfWeek = %s")
        params.append(day)

    if faculty_id != 'All':
        conditions.append("f.FacultyID = %s")
        params.append(faculty_id)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY f.FacultyID, s.DayOfWeek, ts.StartTime"
    cur.execute(query, tuple(params))
    schedules = cur.fetchall()
    cur.close()

    # Group schedules by faculty
    faculty_schedules = {}
    for faculty in faculties:
        faculty_schedules[faculty['FacultyID']] = {
            'faculty': faculty,
            'schedules': [s for s in schedules if s['FacultyID'] == faculty['FacultyID']]
        }

    # If filtering by specific faculty, only show that faculty
    if faculty_id != 'All':
        faculty_schedules = {faculty_id: faculty_schedules.get(int(faculty_id), {'faculty': None, 'schedules': []})}

    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    return render_template('schedule/faculty_timetable_report.html', faculty_schedules=faculty_schedules, day=day, days=days, faculties=faculties, faculty=faculty_id, time_slots=time_slots)

# Student Timetable Report
@app.route('/timetable/student_report', methods=['GET'])
def student_timetable_report():
    program = request.args.get('program', 'All')
    semester = request.args.get('semester', 'All')
    day = request.args.get('day', 'All')

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Fetch programs
    cur.execute("SELECT ProgramID, ProgramName FROM offered_programs")
    programs = cur.fetchall()

    # Fetch semesters
    cur.execute("SELECT SemesterID, SemesterName FROM semesters")
    semesters = cur.fetchall()

    # Days of the week
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

    # Fetch time slots, filter out invalid ones (e.g., duration > 3 hours or specific invalid times)
    cur.execute("""
        SELECT SlotID, StartTime, EndTime
        FROM time_slots
        WHERE TIMEDIFF(EndTime, StartTime) <= '03:00:00'
        AND StartTime NOT IN ('07:38:00', '13:30:00')
        ORDER BY StartTime
    """)
    time_slots = cur.fetchall()

    # Build base query for schedule data with joins, include semester
    query = """
        SELECT s.DayOfWeek, ts.SlotID, ts.StartTime, ts.EndTime, c.CourseName, f.FirstName, f.LastName, r.RoomNumber, sem.SemesterID, sem.SemesterName
        FROM schedule s
        JOIN time_slots ts ON s.SlotID = ts.SlotID
        JOIN courses c ON s.CourseID = c.CourseID
        JOIN faculty f ON s.FacultyID = f.FacultyID
        JOIN rooms r ON s.RoomID = r.RoomID
        JOIN semesters sem ON s.SemesterID = sem.SemesterID
    """
    conditions = []
    params = []

    if program != 'All':
        conditions.append("s.ProgramID = %s")
        params.append(program)

    if semester != 'All':
        conditions.append("s.SemesterID = %s")
        params.append(semester)

    if day != 'All':
        conditions.append("s.DayOfWeek = %s")
        params.append(day)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY sem.SemesterID, s.DayOfWeek, ts.StartTime"

    cur.execute(query, tuple(params))
    schedules = cur.fetchall()

    # Organize data as nested dict: semester -> day -> slot_id -> schedule info
    timetable_by_semester = {}
    for sched in schedules:
        sem_id = sched['SemesterID']
        sem_name = sched['SemesterName']
        d = sched['DayOfWeek']
        slot_id = sched['SlotID']
        if sem_id not in timetable_by_semester:
            timetable_by_semester[sem_id] = {
                'SemesterName': sem_name,
                'timetable': {d: {slot['SlotID']: None for slot in time_slots} for d in days}
            }
        if d in timetable_by_semester[sem_id]['timetable']:
            timetable_by_semester[sem_id]['timetable'][d][slot_id] = {
                'CourseName': sched['CourseName'],
                'FacultyName': f"{sched['FirstName']} {sched['LastName']}",
                'RoomNumber': sched['RoomNumber'],
                'StartTime': sched['StartTime'],
                'EndTime': sched['EndTime'],
                'programName': sched.get('ProgramName'),
                'departmentName': sched.get('DepartmentName')
            }

    return render_template('schedule/student_timetable_report.html',
                           programs=programs,
                           semesters=semesters,
                           days=days,
                           time_slots=time_slots,
                           timetable_by_semester=timetable_by_semester,
                           selected_program=program,
                           selected_semester=semester,
                           selected_day=day)


# Route to list programs (offered_programs)
@app.route('/programs')
def list_programs():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT op.ProgramID, op.ProgramName, s.StartYear, s.EndYear, d.DepartmentName
        FROM offered_programs op
        LEFT JOIN sessions s ON op.SessionID = s.SessionID
        LEFT JOIN departments d ON op.DepartmentID = d.DepartmentID
    """)
    programs = cur.fetchall()
    cur.close()
    return render_template('programs/list_programs.html', programs=programs)

# Route to add a new program (offered_program)
@app.route('/programs/add', methods=['GET', 'POST'])
def add_program():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM sessions")
    sessions = cur.fetchall()
    cur.execute("SELECT * FROM departments")
    departments = cur.fetchall()
    cur.close()
    if request.method == 'POST':
        program_name = request.form['ProgramName']
        session_id = request.form['SessionID']
        department_id = request.form['DepartmentID']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO offered_programs (ProgramName, SessionID, DepartmentID) VALUES (%s, %s, %s)", (program_name, session_id, department_id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_programs'))
    return render_template('programs/add_program.html', sessions=sessions, departments=departments)

# Route to update a program (offered_program)
@app.route('/programs/update/<int:id>', methods=['GET', 'POST'])
def update_program_page(id):   # <-- unique function name
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM offered_programs WHERE ProgramID = %s", (id,))
    program = cur.fetchone()
    cur.execute("SELECT * FROM sessions")
    sessions = cur.fetchall()
    cur.execute("SELECT * FROM departments")
    departments = cur.fetchall()
    cur.close()

    if request.method == 'POST':
        program_name = request.form['ProgramName']
        session_id = request.form['SessionID']
        department_id = request.form['DepartmentID']
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE offered_programs
            SET ProgramName = %s, SessionID = %s, DepartmentID = %s
            WHERE ProgramID = %s
        """, (program_name, session_id, department_id, id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_programs'))

    return render_template(
        'programs/update_program.html',
        program=program,
        sessions=sessions,
        departments=departments
    )

# Route to delete a program (offered_program)
@app.route('/programs/delete/<int:id>', methods=['POST'])
def delete_program(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM offered_programs WHERE ProgramID = %s", (id,))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('list_programs'))
    except Exception as e:
        print(f"Error deleting program: {e}")
        return "An error occurred while deleting the program.", 500

# Edit a scheduled class
@app.route('/schedule/edit/<int:schedule_id>', methods=['GET', 'POST'])
def edit_schedule(schedule_id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""SELECT s.*, op.SessionID, op.DepartmentID FROM schedule s LEFT JOIN offered_programs op ON s.ProgramID = op.ProgramID WHERE s.ScheduleID = %s""", (schedule_id,))
    sched = cur.fetchone()
    cur.execute("SELECT * FROM sessions")
    sessions = cur.fetchall()
    cur.execute("SELECT * FROM departments")
    departments = cur.fetchall()
    cur.execute("SELECT * FROM offered_programs")
    programs = cur.fetchall()
    cur.execute("SELECT * FROM semesters")
    semesters = cur.fetchall()
    cur.execute("SELECT * FROM courses")
    courses = cur.fetchall()
    cur.execute("SELECT * FROM faculty")
    faculty = cur.fetchall()
    cur.execute("SELECT * FROM rooms")
    rooms = cur.fetchall()
    cur.execute("SELECT * FROM time_slots ORDER BY StartTime")
    slots = cur.fetchall()
    cur.close()
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

    if request.method == 'POST':
        program_id = request.form['ProgramID']
        semester_id = request.form['SemesterID']
        course_id = request.form['CourseID']
        faculty_id = request.form['FacultyID']
        room_id = request.form['RoomID']
        slot_id = request.form['SlotID']
        day = request.form['DayOfWeek']

        # Validate ProgramID exists
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT ProgramID FROM offered_programs WHERE ProgramID = %s", (program_id,))
        program_exists = cur.fetchone()
        if not program_exists:
            cur.close()
            flash("Invalid ProgramID: does not exist in offered_programs.", "danger")
            return redirect(url_for('edit_schedule', schedule_id=schedule_id))

        # Conflict check (ignore self)
        cur.execute("""
            SELECT * FROM schedule
            WHERE ScheduleID != %s AND ((RoomID=%s AND SlotID=%s AND DayOfWeek=%s AND SemesterID=%s) OR (FacultyID=%s AND SlotID=%s AND DayOfWeek=%s AND SemesterID=%s))
        """, (schedule_id, room_id, slot_id, day, semester_id, faculty_id, slot_id, day, semester_id))
        conflict = cur.fetchone()
        cur.close()
        if conflict:
            flash("Conflict: Room or Faculty already booked for this slot and day.", "danger")
            return redirect(url_for('edit_schedule', schedule_id=schedule_id))

        cur = mysql.connection.cursor()
        cur.execute(""" 
            UPDATE schedule SET CourseID=%s, FacultyID=%s, RoomID=%s, SlotID=%s, DayOfWeek=%s, SemesterID=%s, ProgramID=%s 
            WHERE ScheduleID=%s 
        """, (course_id, faculty_id, room_id, slot_id, day, semester_id, program_id, schedule_id))
        mysql.connection.commit()
        cur.close()
        flash("Schedule updated successfully!", "success")
        return redirect(url_for('room_timetable'))

    return render_template('schedule/edit_schedule.html', sched=sched, sessions=sessions, departments=departments, programs=programs, courses=courses, faculty=faculty, rooms=rooms, slots=slots, days=days)

# Delete a scheduled class
@app.route('/schedule/delete/<int:schedule_id>', methods=['POST'])
def delete_schedule(schedule_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM schedule WHERE ScheduleID = %s", (schedule_id,))
    mysql.connection.commit()
    cur.close()
    flash("Schedule deleted.", "success")
    return redirect(request.referrer or url_for('room_timetable'))

from flask import session

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        if role == 'admin':
            # Check in admin table
            cur.execute("SELECT * FROM admin WHERE username = %s AND password = %s", (username, password))
            user = cur.fetchone()
        elif role == 'teacher':
            # Check in faculty table
            cur.execute("SELECT * FROM faculty WHERE LOWER(Email) = LOWER(%s) AND password = %s", (username, password))
            user = cur.fetchone()
        elif role == 'student':
            # Check for shared credentials first
            if '@' in username and password == 'student123':  # Common password for shared login
                # Parse email to get program and semester (format: programname_semestername@domain.com)
                email_parts = username.split('@')[0].split('_')
                if len(email_parts) == 2:
                    program_name, semester_name = email_parts
                    # Find program_id and semester_id
                    cur.execute("SELECT op.ProgramID FROM offered_programs op WHERE op.ProgramName = %s", (program_name,))
                    program = cur.fetchone()
                    cur.execute("SELECT s.SemesterID FROM semesters s WHERE s.SemesterName = %s", (semester_name,))
                    semester = cur.fetchone()
                    if program and semester:
                        user = {'ProgramID': program['ProgramID'], 'SemesterID': semester['SemesterID'], 'shared': True}
                    else:
                        user = None
                else:
                    user = None
            else:
                # Fallback to individual student login
                cur.execute("SELECT * FROM students WHERE Email = %s AND password = %s", (username, password))
                user = cur.fetchone()
        else:
            user = None

        cur.close()

        if user:
            session['loggedin'] = True
            session['username'] = username
            session['role'] = role
            if role == 'teacher':
                session['faculty_id'] = user['FacultyID']
                # Redirect to faculty timetable filtered by faculty id
                return redirect(url_for('faculty_timetable', faculty=user['FacultyID']))
            elif role == 'student':
                # Always force students to their timetable, never dashboard
                if user.get('shared'):
                    return redirect(url_for('student_timetable', program_id=user['ProgramID'], semester_id=user['SemesterID']))
                else:
                    session['student_id'] = user['StudentID']
                    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                    cur.execute("SELECT e.SemesterID, op.ProgramID FROM enrolledstudents e JOIN students s ON e.StudentID = s.StudentID JOIN offered_programs op ON op.DepartmentID = s.DepartmentID WHERE e.StudentID = %s LIMIT 1", (user['StudentID'],))
                    enrollment = cur.fetchone()
                    cur.close()
                    if enrollment:
                        return redirect(url_for('student_timetable', program_id=enrollment['ProgramID'], semester_id=enrollment['SemesterID']))
                    else:
                        flash('No enrollment found for your account. Please contact admin.', 'danger')
                        return redirect(url_for('student_timetable'))
            else:
                # Only non-student, non-teacher roles go to dashboard
                return redirect(url_for('dashboard'))
        else:
            flash('Incorrect username/password or role!', 'danger')
            return render_template('login.html')

    return render_template('login.html')


# Logout route
@app.route('/logout')
def logout():
    session.clear()
    resp = make_response(redirect(url_for('login')))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

# Prevent browser caching for all routes (so back button after logout doesn't restore session)
@app.after_request
def add_no_cache_headers(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

from flask import jsonify

# API routes for cascading dropdowns in add_class
@app.route('/api/departments/<int:session_id>')
def api_departments(session_id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT DISTINCT d.DepartmentID, d.DepartmentName FROM departments d JOIN offered_programs op ON d.DepartmentID = op.DepartmentID WHERE op.SessionID = %s", (session_id,))
    departments = cur.fetchall()
    cur.close()
    return jsonify(departments)

@app.route('/api/programs/<int:session_id>/<int:department_id>')
def api_programs(session_id, department_id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT p.ProgramID, p.ProgramName
        FROM offered_programs op
        JOIN programs p ON op.ProgramID = p.ProgramID
        WHERE op.SessionID = %s AND op.DepartmentID = %s
    """, (session_id, department_id))
    programs = cur.fetchall()
    cur.close()
    return jsonify(programs)

@app.route('/api/courses/<int:department_id>')
def api_courses(department_id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT CourseID, CourseName FROM courses WHERE DepartmentID = %s", (department_id,))
    courses = cur.fetchall()
    cur.close()
    return jsonify(courses)

@app.route('/weekly_timetable', methods=['GET'])
def weekly_timetable():
    session_id = request.args.get('session_id', type=int)
    program_id = request.args.get('program_id', type=int)
    semester_id = request.args.get('semester_id', type=int)

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Fetch time slots
    cur.execute("SELECT * FROM time_slots ORDER BY StartTime")
    time_slots = cur.fetchall()

    # Days of the week
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

    # Build base query for schedule entries filtered by session, program, semester
    query = """
        SELECT s.DayOfWeek, s.SlotID, c.CourseName, f.FirstName, f.LastName, r.RoomNumber, sem.SemesterID, sem.SemesterName, ts.StartTime, ts.EndTime, op.ProgramName, d.DepartmentName
        FROM schedule s
        JOIN courses c ON s.CourseID = c.CourseID
        JOIN faculty f ON s.FacultyID = f.FacultyID
        JOIN rooms r ON s.RoomID = r.RoomID
        JOIN offered_programs op ON s.ProgramID = op.ProgramID
        JOIN departments d ON op.DepartmentID = d.DepartmentID
        JOIN semesters sem ON s.SemesterID = sem.SemesterID
        JOIN sessions sess ON op.SessionID = sess.SessionID
        JOIN time_slots ts ON s.SlotID = ts.SlotID
        WHERE 1=1
    """
    params = []

    if session_id:
        query += " AND sess.SessionID = %s"
        params.append(session_id)
    if program_id:
        query += " AND op.ProgramID = %s"
        params.append(program_id)
    if semester_id:
        query += " AND sem.SemesterID = %s"
        params.append(semester_id)

    query += " ORDER BY sem.SemesterID, s.DayOfWeek, ts.StartTime"

    cur.execute(query, tuple(params))
    schedules = cur.fetchall()

    # Organize data as nested dict: semester -> day -> slot_id -> schedule info
    timetable_by_semester = {}
    for sched in schedules:
        sem_id = sched['SemesterID']
        sem_name = sched['SemesterName']
        d = sched['DayOfWeek']
        slot_id = sched['SlotID']
        if sem_id not in timetable_by_semester:
            timetable_by_semester[sem_id] = {
                'SemesterName': sem_name,
                'timetable': {d: {slot['SlotID']: None for slot in time_slots} for d in days}
            }
        if d in timetable_by_semester[sem_id]['timetable']:
            timetable_by_semester[sem_id]['timetable'][d][slot_id] = {
                'CourseName': sched['CourseName'],
                'FacultyName': f"{sched['FirstName']} {sched['LastName']}",
                'RoomNumber': sched['RoomNumber'],
                'StartTime': sched['StartTime'],
                'EndTime': sched['EndTime'],
                'departmentName': sched.get('DepartmentName', ''),
                'programName': sched.get('ProgramName', '')
            }

    # Fetch filter options
    cur.execute("SELECT * FROM sessions ORDER BY StartYear DESC")
    sessions = cur.fetchall()
    cur.execute("SELECT * FROM offered_programs ORDER BY ProgramName")
    programs = cur.fetchall()
    cur.execute("SELECT * FROM semesters ORDER BY SemesterName")
    semesters = cur.fetchall()

    cur.close()

    return render_template('schedule/weekly_timetable.html',
                           time_slots=time_slots,
                           timetable_by_semester=timetable_by_semester,
                           sessions=sessions,
                           programs=programs,
                           semesters=semesters,
                           selected_session=session_id,
                           selected_program=program_id,
                           selected_semester=semester_id,
                           days=days)
if __name__ == '__main__':
    app.run(debug=True)

