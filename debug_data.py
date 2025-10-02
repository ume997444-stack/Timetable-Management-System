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

def debug_data():
    with app.app_context():
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Check each table
        tables = ['students', 'assign_courses_to_student', 'current_semester', 'offered_programs', 'schedule', 'courses', 'faculty', 'rooms', 'time_slots']

        for table in tables:
            cur.execute(f"SELECT COUNT(*) as count FROM {table}")
            count = cur.fetchone()
            print(f"{table}: {count['count']} records")

            if count['count'] > 0:
                cur.execute(f"SELECT * FROM {table} LIMIT 3")
                samples = cur.fetchall()
                print(f"Sample from {table}:")
                for sample in samples:
                    print(f"  {sample}")
                print()

        cur.close()

if __name__ == '__main__':
    debug_data()
