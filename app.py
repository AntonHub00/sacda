from flask import Flask, render_template, session, request, redirect, url_for
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

#secret_key function is needed for session handling
app.secret_key = os.urandom(24)

#check_password_hash(stored_password, password_given_in_form)

#This data shouldn't be filled here (could use a yaml config file instead)
#'localhost' doesn't work, just with '127.0.0.1' ('localhost' = '127.0.0.1')
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'fis_practice'
mysql = MySQL(app)
#use "mysql.connection.commit()" if you are making an insert into a table or an update (you need to tell mysql object to commit that query)

#This global variable makes it posible to open/close database connection with before_request/after_request decorators
cur = None

@app.before_request
def before_request():
    global cur

    try:
        cur = mysql.connection.cursor()
    except:
        return 'No se puede conectar con la base de datos'

@app.after_request
def after_request(response):
    global cur

    try:
        cur.close()
    except:
        return 'No se pudo cerrar la conexión con la base de datos'

    return response

@app.route('/')
def index():
    return render_template('main/index.html')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        #TODO: Validate whether the user exists (could verify if rows (registers) > 0; it means user exists)
        user = request.form['user']
        password = request.form['password']

        try:
            cur.execute(f''' SELECT ContraProf, sistema FROM profesionista WHERE RFC_Profesor = '{user}' ''')
            query_result = cur.fetchall()
            r_password = query_result[0][0]
            system_flag = query_result[0][1]
        except:
            return 'Hubo un problema al obtener la información de la base de datos'

        #Checking if the password given is correct and is a registered user
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

@app.route('/administrador')
@app.route('/administrador/')
@app.route('/administrador/inicio')
def admin_home():
    return render_template('admin/home.html', active = 'admin_home')

@app.route('/administrador/profesionales/alta', methods = ['GET', 'POST'])
def admin_professionals_subscribe():
    if request.method == 'POST':
        data = {}

        data['name'] = request.form['name']
        data['first_last_name'] = request.form['first_last_name']
        data['second_last_name'] = request.form['second_last_name']
        data['rfc'] = request.form['rfc']
        data['email'] = request.form['email']
        data['phone'] = request.form['phone']
        data['job'] = request.form['job']
        data['entry_time'] = request.form['entry_time']
        data['exit_time'] = request.form['exit_time']
        data['place'] = request.form['place']
        data['password'] = request.form['password']

        #Check whether the fields are filled
        if '' in data.values():
            #Teporary solution to check the validation (Must show a error message)
            return redirect(url_for('login'))
        else:
            try:
                cur.execute(f''' SELECT cve_puesto FROM puesto WHERE desc_puesto = '{data['job']}' ''')
                data['job'] = cur.fetchall()[0][0]

                cur.execute(f''' SELECT CveLugar FROM lugar WHERE DescLugar = '{data['place']}' ''')
                data['place'] = cur.fetchall()[0][0]
            except:
                return 'Hubo un problema al obtener la información de la base de datos'

            data['password'] = generate_password_hash(data['password'], method = 'sha256')

            try:
                cur.execute(f'''INSERT INTO profesionista VALUES('{data['rfc']}', '{data['name']}', '{data['first_last_name']}', '{data['second_last_name']}', '{data['email']}', '{data['phone']}', '{data['rfc']}', {data['job']}, '{data['password']}', '{data['entry_time']}', '{data['exit_time']}', {data['place']}, 1)''')
            except:
                return 'Hubo un problema al guadar la información en la base de datos'

            mysql.connection.commit()

            #Implement message of success instead
            return 'Profesionista registrado con éxito'

    try:
        cur.execute(''' SELECT * FROM lugar''')
        r_place = cur.fetchall()

        cur.execute(''' SELECT * FROM puesto''')
        r_job = cur.fetchall()
    except:
        return 'Hubo un problema al obtener la información de la base de datos'


    return render_template('admin/professionals_subscribe.html', active = 'admin_professionals', r_place = r_place, r_job = r_job)

@app.route('/administrador/profesionales/baja', methods = ['GET', 'POST'])
def admin_professionals_unsubscribe():
    if request.method == 'POST':
        professional_key = request.form['to_delete']

        try:
            cur.execute(f''' UPDATE profesionista SET sistema = 0 WHERE RFC_Profesor = '{professional_key}' ''')
        except:
            return 'Hubo un problema al actualizar la información en la base de datos'

        mysql.connection.commit()

        return redirect(url_for('admin_professionals_unsubscribe'))

    try:
        cur.execute(''' SELECT RFC_Profesor, NombreProf, Primer_ApellidoP, Segundo_ApellidoP, puesto.desc_puesto, lugar.DescLugar, HorarioEntrada, HorarioSalida, CorreoP, TelProf FROM profesionista INNER JOIN lugar ON profesionista.Lugar = lugar.CveLugar INNER JOIN puesto ON profesionista.PuestoProf = puesto.cve_puesto WHERE sistema = 1''')
        r_professionals = cur.fetchall()
    except:
        return 'Hubo un problema al obtener la información de la base de datos'

    return render_template('admin/professionals_unsubscribe.html', active = 'admin_professionals', r_professionals = r_professionals)

@app.route('/administrador/profesionales/modificar')
def admin_professionals_modify():
    return render_template('admin/professionals_modify.html', active = 'admin_professionals')
#End of professionals---------------------------------------

#Beginning of students---------------------------------------
@app.route('/administrador/estudiantes/modificar')
def admin_students_modify():
    return render_template('admin/students_modify.html', active = 'admin_students')

@app.route('/administrador/estudiantes/baja')
def admin_students_unsubscribe():
    return render_template('admin/students_unsubscribe.html', active = 'admin_students')
#End of students---------------------------------------

@app.route('/administrador/agendas')
def admin_schedule():
    return render_template('admin/schedule.html', active = 'admin_schedule')

#Beginning of statistics---------------------------------------
@app.route('/administrador/estadisticas/generales')
def admin_statistics_general():
    return render_template('admin/statistics_general.html', active = 'admin_statistics')

@app.route('/administrador/estadisticas/profesionistas')
def admin_statistics_professionals():
    return render_template('admin/statistics_professionals.html', active = 'admin_statistics')

@app.route('/administrador/estadisticas/canalizaciones')
def admin_statistics_canalization():
    return render_template('admin/statistics_canalization.html', active = 'admin_statistics')
#End of statistics---------------------------------------
# End of Admin Views ###########################################################################################

# Beginning of Profesional Views ###########################################################################################
@app.route('/profesionista')
@app.route('/profesionista/')
@app.route('/profesionista/inicio')
def professional_home():
    if 'user' in session:
        try:
            cur.execute(f'''SELECT NombreProf FROM profesionista WHERE RFC_Profesor = '{session['user']}' ''')
            professional_name = cur.fetchall()[0][0]
        except:
            return 'Hubo un problema al obtener la información de la base de datos'

        return render_template('professional/home.html', active = 'professional_home', professional_name = professional_name)

    return 'Necesitas iniciar sesión primero'

@app.route('/profesionista/agenda')
def professional_schedule():
    if 'user' in session:
        return render_template('professional/schedule.html', active = 'professional_schedule')

    return 'Necesitas iniciar sesión primero'

@app.route('/profesionista/datos')
def professional_data():
    if 'user' in session:
        return render_template('professional/data.html', active = 'professional_data')

    return 'Necesitas iniciar sesión primero'

# End of Profesional Views ###########################################################################################
if __name__ == '__main__':
    app.run(debug = True)

