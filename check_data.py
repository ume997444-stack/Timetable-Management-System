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

def check_data():
    with app.app_context():
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Check if table exists
        cur.execute("SHOW TABLES LIKE 'student_timetable_reports'")
        table_exists = cur.fetchone()
        print(f"Table exists: {table_exists}")

        if table_exists:
            # Check count
            cur.execute("SELECT COUNT(*) as count FROM student_timetable_reports")
            count = cur.fetchone()
            print(f"Records in table: {count['count']}")

            # Check sample data
            cur.execute("SELECT * FROM student_timetable_reports LIMIT 5")
            samples = cur.fetchall()
            print("Sample records:")
            for sample in samples:
                print(sample)

        cur.close()

if __name__ == '__main__':
    check_data()
