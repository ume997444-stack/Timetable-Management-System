from flask import Flask
from flask_mysqldb import MySQL
import MySQLdb.cursors

app = Flask(__name__)
app.secret_key = 'your-very-secret-key'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'timetable_attendance'

mysql = MySQL(app)

with app.app_context():
    cur = mysql.connection.cursor()
    cur.execute("DESCRIBE faculty")
    result = cur.fetchall()
    print("Faculty table structure:")
    for row in result:
        print(row)

    cur.execute("SELECT FacultyID, FirstName, LastName, Email, Password FROM faculty WHERE FirstName LIKE %s OR LastName LIKE %s", ('%Anmol%', '%Bibi%'))
    faculty = cur.fetchall()
    print("Faculty matching Anmol or Bibi:")
    for f in faculty:
        print(f)

    cur.close()
