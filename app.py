from flask import Flask, render_template, session
from flask_mysqldb import MySQL
import os

app = Flask(__name__)
#app.secret_key = os.urandom(24)

#This data shouldn't be filled here (could use a yaml config file)
#app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'fis_practice'
mysql = MySQL(app)

@app.route('/')
def index():
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM profesionista''')
    #use mysql.connection.commit()
    #if you are making an insert into the table (you need to tell mysql objecto to commit that query)
    rv = cur.fetchall()
    cur.close()
    return str(rv[0][1])
    #return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/logout')
def logout():
    return render_template('logout.html')

# Beginning of Admin Views ###########################################################################################
@app.route('/admin_home')
def admin_home():
    return render_template('admin_home.html', active = 'admin_home')

#Beginning of professionals---------------------------------------
@app.route('/admin_professionals_subscribe')
def admin_professionals_subscribe():
    return render_template('admin_professionals_subscribe.html', active = 'admin_professionals')

@app.route('/admin_professionals_unsubscribe')
def admin_professionals_unsubscribe():
    return render_template('admin_professionals_unsubscribe.html', active = 'admin_professionals')

@app.route('/admin_professionals_modify')
def admin_professionals_modify():
    return render_template('admin_professionals_modify.html', active = 'admin_professionals')
#End of professionals---------------------------------------

#Beginning of students---------------------------------------
@app.route('/admin_students_modify')
def admin_students_modify():
    return render_template('admin_students_modify.html', active = 'admin_students')

@app.route('/admin_students_unsubscribe')
def admin_students_unsubscribe():
    return render_template('admin_students_unsubscribe.html', active = 'admin_students')
#End of students---------------------------------------

@app.route('/admin_schedule')
def admin_schedule():
    return render_template('admin_schedule.html', active = 'admin_schedule')

#Beginning of statistics---------------------------------------
@app.route('/admin_statistics_general')
def admin_statistics_general():
    return render_template('admin_statistics_general.html', active = 'admin_statistics')

@app.route('/admin_statistics_professionals')
def admin_statistics_professionals():
    return render_template('admin_statistics_professionals.html', active = 'admin_statistics')

@app.route('/admin_statistics_canalization')
def admin_statistics_canalization():
    return render_template('admin_statistics_canalization.html', active = 'admin_statistics')
#End of statistics---------------------------------------
# End of Admin Views ###########################################################################################

# Beginning of Profesional Views ###########################################################################################
@app.route('/professional_home')
def professional_home():
    return render_template('professional_home.html', active = 'professional_home')

@app.route('/professional_schedule')
def professional_schedule():
    return render_template('professional_schedule.html', active = 'professional_schedule')

@app.route('/professional_data')
def professional_data():
    return render_template('professional_data.html', active = 'professional_data')

# End of Profesional Views ###########################################################################################
if __name__ == '__main__':
    app.run(debug = True)
