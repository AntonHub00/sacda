from flask import Flask, render_template, session, request, redirect, url_for
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

#secret_key function is needed for session handling
app.secret_key = os.urandom(24)

#check_password_hash(stored_password, password_given_in_form)

#This data shouldn't be filled here (could use a yaml config file)
#'localhost' doesn't work, just with '127.0.0.1' ('localhost' = '127.0.0.1')
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'fis_practice'
mysql = MySQL(app)
#use "mysql.connection.commit()" if you are making an insert into a table (you need to tell mysql object to commit that query)

@app.route('/')
def index():
    return render_template('main/index.html')

#JSON web tokens

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        cur = mysql.connection.cursor()

        user = request.form['user']
        password = request.form['password']

        cur.execute(f''' SELECT ContraProf, sistema FROM profesionista WHERE RFC_Profesor = '{user}' ''')
        query_result = cur.fetchall()
        #TODO: Validate user exists (could verify if rows (registers) > 0; it means user exists)
        r_password = query_result[0][0]
        system_flag = query_result[0][1]

        cur.close()

        if check_password_hash(r_password, password) and system_flag == 1:
            session['user'] = user

    if 'user' in session:
        return redirect(url_for('professional_home'))
    return render_template('main/login.html')

@app.route('/logout')
def logout():
    if 'user' in session:
        session.pop('user', None)

    return redirect(url_for('login'))

# Beginning of Admin Views ###########################################################################################
@app.route('/admin_home')
def admin_home():
    return render_template('admin/home.html', active = 'admin_home')

#Beginning of professionals---------------------------------------
@app.route('/admin_professionals_subscribe', methods = ['GET', 'POST'])
def admin_professionals_subscribe():
    if request.method == 'POST':
        cur = mysql.connection.cursor()

        name = request.form['name']
        first_last_name = request.form['first_last_name']
        second_last_name = request.form['second_last_name']
        rfc = request.form['rfc']
        email = request.form['email']
        phone = request.form['phone']
        job = request.form['job']
        cur.execute(f''' SELECT cve_puesto FROM puesto WHERE desc_puesto = '{job}' ''')
        job = cur.fetchall()[0][0]
        entry_time = request.form['entry_time']
        exit_time = request.form['exit_time']
        place = request.form['place']
        cur.execute(f''' SELECT CveLugar FROM lugar WHERE DescLugar = '{place}' ''')
        place = cur.fetchall()[0][0]
        password = generate_password_hash(request.form['password'], method = 'sha256')

        cur.execute(f'''INSERT INTO profesionista VALUES('{rfc}', '{name}', '{first_last_name}', '{second_last_name}', '{email}', '{phone}', '{rfc}', {job}, '{password}', '{entry_time}', '{exit_time}', {place}, 1)''')
        mysql.connection.commit()
        cur.close()

        #cur.execute(''' SELECT * FROM profesionista''')
        #result_prof = cur.fetch_all()
        return 'Done!'
        #return result_prof

    cur = mysql.connection.cursor()
    cur.execute(''' SELECT * FROM lugar''')
    r_place = cur.fetchall()
    cur.execute(''' SELECT * FROM puesto''')
    r_job = cur.fetchall()
    cur.close()
    return render_template('admin/professionals_subscribe.html', active = 'admin_professionals', r_place = r_place, r_job = r_job)

@app.route('/admin_professionals_unsubscribe', methods = ['GET', 'POST'])
def admin_professionals_unsubscribe():
    if request.method == 'POST':
        professional_key = request.form['to_delete']
        cur = mysql.connection.cursor()
        cur.execute(f''' SELECT sistema FROM profesionista WHERE RFC_Profesor = '{professional_key}' ''')
        in_system = cur.fetchall()[0][0]
        cur.close()
        if in_system == 1:
            cur = mysql.connection.cursor()
            cur.execute(f''' UPDATE profesionista SET sistema = 0 WHERE RFC_Profesor = '{professional_key}' ''')
            mysql.connection.commit()
            cur.close()

        return redirect(url_for('admin_professionals_unsubscribe'))

    cur = mysql.connection.cursor()
    cur.execute(''' SELECT RFC_Profesor, NombreProf, Primer_ApellidoP, Segundo_ApellidoP, puesto.desc_puesto, lugar.DescLugar, HorarioEntrada, HorarioSalida, CorreoP, TelProf, sistema FROM profesionista INNER JOIN lugar ON profesionista.Lugar = lugar.CveLugar INNER JOIN puesto ON profesionista.PuestoProf = puesto.cve_puesto''')
    r_professionals = cur.fetchall()
    cur.close()

    return render_template('admin/professionals_unsubscribe.html', active = 'admin_professionals', r_professionals = r_professionals)

@app.route('/admin_professionals_modify')
def admin_professionals_modify():
    return render_template('admin/professionals_modify.html', active = 'admin_professionals')
#End of professionals---------------------------------------

#Beginning of students---------------------------------------
@app.route('/admin_students_modify')
def admin_students_modify():
    return render_template('admin/students_modify.html', active = 'admin_students')

@app.route('/admin_students_unsubscribe')
def admin_students_unsubscribe():
    return render_template('admin/students_unsubscribe.html', active = 'admin_students')
#End of students---------------------------------------

@app.route('/admin_schedule')
def admin_schedule():
    return render_template('admin/schedule.html', active = 'admin_schedule')

#Beginning of statistics---------------------------------------
@app.route('/admin_statistics_general')
def admin_statistics_general():
    return render_template('admin/statistics_general.html', active = 'admin_statistics')

@app.route('/admin_statistics_professionals')
def admin_statistics_professionals():
    return render_template('admin/statistics_professionals.html', active = 'admin_statistics')

@app.route('/admin_statistics_canalization')
def admin_statistics_canalization():
    return render_template('admin/statistics_canalization.html', active = 'admin_statistics')
#End of statistics---------------------------------------
# End of Admin Views ###########################################################################################

# Beginning of Profesional Views ###########################################################################################
@app.route('/professional_home')
def professional_home():
    if 'user' in session:
        cur = mysql.connection.cursor()
        cur.execute(f'''SELECT NombreProf FROM profesionista WHERE RFC_Profesor = '{session['user']}' ''')
        professional_name = cur.fetchall()[0][0]
        cur.close()
        return render_template('professional/home.html', active = 'professional_home', professional_name = professional_name)

    return 'Necesitas iniciar sesión primero'

@app.route('/professional_schedule')
def professional_schedule():
    if 'user' in session:
        return render_template('professional/schedule.html', active = 'professional_schedule')

    return 'Necesitas iniciar sesión primero'

@app.route('/professional_data')
def professional_data():
    if 'user' in session:
        return render_template('professional/data.html', active = 'professional_data')

    return 'Necesitas iniciar sesión primero'

# End of Profesional Views ###########################################################################################
if __name__ == '__main__':
    app.run(debug = True)
