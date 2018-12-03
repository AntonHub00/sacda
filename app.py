from flask import Flask, render_template, session, request, redirect, url_for
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
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
app.config['MYSQL_DB'] = 'sacda_5'
mysql = MySQL(app) #use "mysql.connection.commit()" if you are making an insert into a table or an update (you need to tell mysql object to commit that query)
cur = None #This global variable (cursor) makes it posible to open/close database connection with before_request/after_request decorators
roles = {'professional' : 1, 'student' : 2, 'admin' : 3}

def requires_access_level_and_session(access_level):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session:
                return redirect(url_for('login'))

            try:
                cur.execute(f''' SELECT Rol FROM profesionista WHERE RFC_Profesor = '{session['user']}' ''')
                professional = cur.fetchall()

                cur.execute(f''' SELECT Rol FROM administrador WHERE RFC_Prof = '{session['user']}' ''')
                admin = cur.fetchall()

                cur.execute(f''' SELECT Rol FROM alumno WHERE MatAlum = '{session['user']}' ''')
                student = cur.fetchall()

                if professional:
                    role = professional[0][0]
                elif admin:
                    role = admin[0][0]
                elif student:
                    role = student[0][0]
            except:
                return 'Hubo un problema al obtener la información de la base de datos'

            if role != access_level:
                return 'No tienes permiso para acceder a esta página'
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.before_request
def before_request():
    global cur

    try:
        cur = mysql.connection.cursor()
    except:
        return 'No se puede conectar con la base de datos'

@app.teardown_request
def teardown_request(error):
    try:
        cur.close()
    except:
        return 'No se pudo cerrar la conexión con la base de datos'

@app.route('/')
def index():
    return render_template('main/index.html')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['user']
        password = request.form['password']
        redirect_user = None

        try:
            cur.execute(f''' SELECT ContraProf, Sistema FROM profesionista WHERE RFC_Profesor = '{user}' ''')
            professional = cur.fetchall()

            cur.execute(f''' SELECT ContraAdmin FROM administrador WHERE RFC_Prof = '{user}' ''')
            admin = cur.fetchall()

            cur.execute(f''' SELECT ContraAlum FROM alumno WHERE MatAlum = '{user}' ''')
            student = cur.fetchall()

            if professional:
                r_password = professional[0][0]
                system_flag = professional[0][1]
                redirect_user = 'professional_home'
            elif admin:
                r_password = admin[0][0]
                redirect_user = 'admin_home'
            elif student:
                r_password = student[0][0]
                redirect_user = 'login'
            else:
                return redirect(url_for('login'))
        except:
            return 'Hubo un problema al obtener la información de la base de datos'

        #Checking if the password given is correct and is a registered user
        #TODO: add "in system" flags to student and admin
        if check_password_hash(r_password, password):
            session['user'] = user

        return redirect(url_for(redirect_user))

    return render_template('main/login.html')

@app.route('/logout')
def logout():
    if 'user' in session:
        session.pop('user', None)

    return redirect(url_for('login'))

@app.route('/administrador')
@app.route('/administrador/')
@app.route('/administrador/inicio')
@requires_access_level_and_session(roles['admin'])
def admin_home():
    return render_template('admin/home.html', active = 'admin_home')

@app.route('/administrador/profesionales/alta', methods = ['GET', 'POST'])
@requires_access_level_and_session(roles['admin'])
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
            return 'Los campos no pueden estar vacíos'
        elif not data['phone'].isdigit():
            return 'El campo teléfono solo debe contener dígitos'
        else:
            try:
                cur.execute(f''' SELECT NombreProf FROM profesionista WHERE RFC_Profesor= '{data['rfc']}' ''')
                user = cur.fetchall()
            except:
                return 'Hubo un problema al guadar la información en la base de datos'

            if user != ():
                return 'Ya existe un usuario registrado con ese RFC'

            try:
                cur.execute(f''' SELECT CvePuesto FROM puesto WHERE DescPuesto = '{data['job']}' ''')
                data['job'] = cur.fetchall()[0][0]

                cur.execute(f''' SELECT CveLugar FROM lugar WHERE DescLugar = '{data['place']}' ''')
                data['place'] = cur.fetchall()[0][0]
            except:
                return 'Hubo un problema al obtener la información de la base de datos'

            data['password'] = generate_password_hash(data['password'], method = 'sha256')

            try:
                cur.execute(f'''INSERT INTO profesionista VALUES('{data['rfc']}', '{data['name']}', '{data['first_last_name']}', '{data['second_last_name']}', '{data['email']}', '{data['phone']}', '{data['rfc']}', {data['job']}, '{data['password']}', '{data['entry_time']}', '{data['exit_time']}', {data['place']}, 1, 1)''')
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
@requires_access_level_and_session(roles['admin'])
def admin_professionals_unsubscribe():
    if request.method == 'POST':
        professional_key = request.form['to_delete']

        try:
            cur.execute(f''' UPDATE profesionista SET Sistema = 0 WHERE RFC_Profesor = '{professional_key}' ''')
        except:
            return 'Hubo un problema al actualizar la información en la base de datos'

        mysql.connection.commit()

        return redirect(url_for('admin_professionals_unsubscribe'))

    try:
        cur.execute(''' SELECT RFC_Profesor, NombreProf, Primer_ApellidoP, Segundo_ApellidoP, puesto.DescPuesto, lugar.DescLugar, HorarioEntrada, HorarioSalida, CorreoP, TelProf FROM profesionista INNER JOIN lugar ON profesionista.Lugar = lugar.CveLugar INNER JOIN puesto ON profesionista.Puesto = puesto.CvePuesto WHERE Sistema = 1''')
        r_professionals = cur.fetchall()
    except:
        return 'Hubo un problema al obtener la información de la base de datos'

    return render_template('admin/professionals_unsubscribe.html', active = 'admin_professionals', r_professionals = r_professionals)

@app.route('/administrador/profesionales/modificar')
@requires_access_level_and_session(roles['admin'])
def admin_professionals_modify():
    return render_template('admin/professionals_modify.html', active = 'admin_professionals')

@app.route('/administrador/estudiantes/modificar')
@requires_access_level_and_session(roles['admin'])
def admin_students_modify():
    return render_template('admin/students_modify.html', active = 'admin_students')

@app.route('/administrador/estudiantes/baja')
@requires_access_level_and_session(roles['admin'])
def admin_students_unsubscribe():
    return render_template('admin/students_unsubscribe.html', active = 'admin_students')

@app.route('/administrador/agendas')
@requires_access_level_and_session(roles['admin'])
def admin_schedule():
    return render_template('admin/schedule.html', active = 'admin_schedule')

@app.route('/administrador/estadisticas/generales')
@requires_access_level_and_session(roles['admin'])
def admin_statistics_general():
    return render_template('admin/statistics_general.html', active = 'admin_statistics')

@app.route('/administrador/estadisticas/profesionistas')
@requires_access_level_and_session(roles['admin'])
def admin_statistics_professionals():
    return render_template('admin/statistics_professionals.html', active = 'admin_statistics')

@app.route('/administrador/estadisticas/canalizaciones')
@requires_access_level_and_session(roles['admin'])
def admin_statistics_canalization():
    return render_template('admin/statistics_canalization.html', active = 'admin_statistics')

@app.route('/profesionista')
@app.route('/profesionista/')
@app.route('/profesionista/inicio')
@requires_access_level_and_session(roles['professional'])
def professional_home():
    try:
        cur.execute(f'''SELECT NombreProf FROM profesionista WHERE RFC_Profesor = '{session['user']}' ''')
        professional_name = cur.fetchall()[0][0]
    except:
        return 'Hubo un problema al obtener la información de la base de datos'

    return render_template('professional/home.html', active = 'professional_home', professional_name = professional_name)

@app.route('/profesionista/agenda')
@requires_access_level_and_session(roles['professional'])
def professional_schedule():
    return render_template('professional/schedule.html', active = 'professional_schedule')

@app.route('/profesionista/datos')
@requires_access_level_and_session(roles['professional'])
def professional_data():
    try:
        cur.execute(f'''SELECT NombreProf, Primer_ApellidoP , Segundo_ApellidoP, CorreoP, TelProf, DescPuesto, HorarioEntrada, HorarioSalida, DescLugar FROM profesionista INNER JOIN lugar ON profesionista.Lugar = lugar.CveLugar INNER JOIN puesto ON profesionista.Puesto = puesto.CvePuesto WHERE RFC_Profesor = '{session['user']}' ''')
        professional_data = cur.fetchall()
    except:
        return 'Hubo un problema al guadar la información en la base de datos'

    return render_template('professional/data.html', active = 'professional_data', professional_data = professional_data)

if __name__ == '__main__':
    app.run(debug = True)

