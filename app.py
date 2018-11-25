from flask import Flask, render_template, session, request, redirect, url_for
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
#secret_key function is needed for session handling
app.secret_key = os.urandom(24)

#check_password_hash(returned_data[0][2], password)

#This data shouldn't be filled here (could use a yaml config file)
#app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'fis_practice'
mysql = MySQL(app)

@app.route('/')
def index():
    return render_template('index.html')

#JSON web tokens

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        cur = mysql.connection.cursor()
        user = request.form['usuario']
        password = request.form['contraseña']
        cur.execute(f''' SELECT  ContraProf FROM profesionista WHERE RFC_Profesor = '{user}' ''')
        r_password = cur.fetchall()[0][0]
        cur.execute(f''' SELECT  sistema FROM profesionista WHERE RFC_Profesor = '{user}' ''')
        system_flag = cur.fetchall()[0][0]
        cur.close()

        if check_password_hash(r_password, password) and system_flag == 1:
            session['user'] = user

    if 'user' in session:
        return redirect(url_for('professional_home'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    if 'user' in session:
        session.pop('user', None)

    return redirect(url_for('login'))

# Beginning of Admin Views ###########################################################################################
@app.route('/admin_home')
def admin_home():
    return render_template('admin_home.html', active = 'admin_home')

#Beginning of professionals---------------------------------------
@app.route('/admin_professionals_subscribe', methods = ['GET', 'POST'])
def admin_professionals_subscribe():
    if request.method == 'POST':
        cur = mysql.connection.cursor()

        nombre = request.form['nombre']
        apellidoMaterno = request.form['apellidoMaterno']
        apellidoPaterno = request.form['apellidoPaterno']
        rfc = request.form['rfc']
        correo = request.form['correo']
        telefono = request.form['telefono']
        puesto = request.form['puesto']
        cur.execute(f''' SELECT cve_puesto FROM puesto WHERE desc_puesto = '{puesto}' ''')
        puesto = cur.fetchall()[0][0]
        horaEntrada = request.form['horaEntrada']
        horaSalida = request.form['horaSalida']
        lugar = request.form['lugar']
        cur.execute(f''' SELECT CveLugar FROM lugar WHERE DescLugar = '{lugar}' ''')
        lugar = cur.fetchall()[0][0]
        contraseña = generate_password_hash(request.form['contraseña'], method = 'sha256')

        cur.execute(f'''INSERT INTO profesionista VALUES('{rfc}', '{nombre}', '{apellidoPaterno}', '{apellidoMaterno}', '{correo}', '{telefono}', '{rfc}', {puesto}, '{contraseña}', '{horaEntrada}', '{horaSalida}', {lugar}, 1)''')
        mysql.connection.commit()
        cur.close()

        #cur.execute(''' SELECT * FROM profesionista''')
        #result_prof = cur.fetch_all()
        return 'Done!'
        #return result_prof

    cur = mysql.connection.cursor()
    cur.execute(''' SELECT * FROM lugar''')
    r_lugar = cur.fetchall()
    cur.execute(''' SELECT * FROM puesto''')
    r_puesto = cur.fetchall()
    cur.close()
    return render_template('admin_professionals_subscribe.html', active = 'admin_professionals', r_lugar = r_lugar, r_puesto = r_puesto)

@app.route('/admin_professionals_unsubscribe', methods = ['GET', 'POST'])
def admin_professionals_unsubscribe():
    if request.method == 'POST':
        key = request.form['enviar']
        cur = mysql.connection.cursor()
        cur.execute(f''' SELECT sistema FROM profesionista WHERE RFC_Profesor = '{key}' ''')
        value = cur.fetchall()[0][0]
        print(type(value))
        cur.close()
        if value == 1:
            cur = mysql.connection.cursor()
            cur.execute(f''' UPDATE profesionista SET sistema = 0 WHERE RFC_Profesor = '{key}' ''')
            mysql.connection.commit()
            cur.close()

        return redirect(url_for('admin_professionals_unsubscribe'))

    cur = mysql.connection.cursor()
    cur.execute(''' SELECT RFC_Profesor, NombreProf, Primer_ApellidoP, Segundo_ApellidoP, puesto.desc_puesto, lugar.DescLugar, HorarioEntrada, HorarioSalida, CorreoP, TelProf, sistema FROM profesionista INNER JOIN lugar ON profesionista.Lugar = lugar.CveLugar INNER JOIN puesto ON profesionista.PuestoProf = puesto.cve_puesto''')
    r_professionals = cur.fetchall()
    cur.close()

    return render_template('admin_professionals_unsubscribe.html', active = 'admin_professionals', r_professionals = r_professionals)

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
    if 'user' in session:
        cur = mysql.connection.cursor()
        cur.execute(f'''SELECT NombreProf FROM profesionista WHERE RFC_Profesor = '{session['user']}' ''')
        professional_name = cur.fetchall()[0][0]
        cur.close()
        return render_template('professional_home.html', active = 'professional_home', professional_name = professional_name)

    return 'Necesitas iniciar sesión primero'

@app.route('/professional_schedule')
def professional_schedule():
    if 'user' in session:
        return render_template('professional_schedule.html', active = 'professional_schedule')

    return 'Necesitas iniciar sesión primero'

@app.route('/professional_data')
def professional_data():
    if 'user' in session:
        return render_template('professional_data.html', active = 'professional_data')

    return 'Necesitas iniciar sesión primero'

# End of Profesional Views ###########################################################################################
if __name__ == '__main__':
    app.run(debug = True)


#cur = mysql.connection.cursor()
#cur.execute(''' SELECT * FROM profesionista''')
##use mysql.connection.commit()
##if you are making an insert into the table (you need to tell mysql objecto to commit that query)
#rv = cur.fetchall()
#cur.close()
#return str(rv[0][1])
