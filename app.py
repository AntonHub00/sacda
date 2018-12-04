from flask import Flask, render_template, session, request, redirect, url_for
from flask_mysqldb import MySQL
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os

app = Flask(__name__)

#secret_key function is needed for session handling
app.secret_key = os.urandom(24)

#This data shouldn't be filled here (could use a yaml config file instead)
#Email configuration
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'test.app.flask@gmail.com'
app.config['MAIL_PASSWORD'] = 'test_app_123'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

#This data shouldn't be filled here (could use a yaml config file instead)
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'sacda_5'

mysql = MySQL(app)
mail = Mail(app)
cur = None #This global variable (cursor) makes it posible to open/close database connection with before_request/after_request decorators
roles = {'professional' : 1, 'student' : 2, 'admin' : 3}
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

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

@app.route('/restablecer', methods = ['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        user = request.form['user']

        try:
            cur.execute(f''' SELECT CorreoP, NombreProf FROM profesionista WHERE RFC_Profesor = '{user}' ''')
            professional = cur.fetchall()

            cur.execute(f''' SELECT CorreoAdmin, NombreAdm FROM administrador WHERE RFC_Prof = '{user}' ''')
            admin = cur.fetchall()

            cur.execute(f''' SELECT CorreoAlum, NombreAlum FROM alumno WHERE MatAlum = '{user}' ''')
            student = cur.fetchall()

            if professional:
                user_mail = professional[0][0]
                user_name = professional[0][1]
                user_identifier_field = 'RFC_Profesor'
                user_role_field = 'profesionista'
                user_password_field = 'ContraProf'
            elif admin:
                user_mail = admin[0][0]
                user_name = admin[0][1]
                user_identifier_field = 'RFC_Prof'
                user_role_field = 'administrador'
                user_password_field = 'ContraAdmin'
            elif student:
                user_mail = student[0][0]
                user_name = student[0][1]
                user_identifier_field = 'MatAlum'
                user_role_field = 'alumno'
                user_password_field = 'ContraAlum'
            else:
                return render_template('main/reset_password.html', sent = False)
        except:
            return 'Hubo un problema al obtener la información de la base de datos'

        user_data = {'user': user, 'identifier_field' : user_identifier_field, 'role_field' : user_role_field, 'password_field' : user_password_field}
        token =  serializer.dumps(user_data, salt = 'reset-password')
        link = url_for('change_password', token = token, _external = True)

        msg = Message('Restablecimiento de contraseña SACDA', sender = 'test.app.flask@gmail.com', recipients = [user_mail])
        msg.body = f'Hola {user_name}. Necesitas entrar a este link para poder restablecer tu contraseña (solo funcionará por 15 minutos): {link}'
        mail.send(msg)

        return render_template('main/reset_password.html', sent = True)

    return render_template('main/reset_password.html', sent = 'unknown')

@app.route('/restablecer/<token>', methods = ['GET', 'POST'])
def change_password(token):
    if request.method == 'POST':
        new_password = request.form['new_password']

        try:
            user_data = serializer.loads(token, salt = 'reset-password', max_age = 900)
        except SignatureExpired:
            return 'Esta página ya no se encuentra disponible (tiempo excedido)'
        except BadTimeSignature:
            return 'El link de verificación no es correcto o fue alterado'

        new_password = generate_password_hash(new_password, method = 'sha256')
        cur.execute(f''' UPDATE {user_data['role_field']} SET {user_data['password_field']} = '{new_password}' WHERE {user_data['identifier_field']} = '{user_data['user']}' ''')
        mysql.connection.commit()

        return redirect(url_for('login'))

    return render_template('main/change_password.html', token = token)

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
                redirect_user = 'student_home'
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

            if user:
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
#INICIO
@app.route('/administrador/estudiantes/alta', methods = ['GET', 'POST'])
@requires_access_level_and_session(roles['admin'])
def admin_students_subscribe():
    if request.method == 'POST':
        data = {}

        data['name'] = request.form['name']
        data['first_last_name'] = request.form['first_last_name']
        data['second_last_name'] = request.form['second_last_name']
        data['enrollment'] = request.form['enrollment']
        data['email'] = request.form['email']
        data['phone'] = request.form['phone']
        data['career'] = request.form['career']
        data['gender'] = request.form['gender']
        data['semester'] = request.form['semester']
        data['password'] = request.form['password']
        #Tutor
        data['name_tutor'] = request.form['name_tutor']
        data['first_last_name_tutor'] = request.form['first_last_name_tutor']
        data['second_last_name_tutor'] = request.form['second_last_name_tutor']
        data['phone_tutor'] = request.form['phone_tutor']
        data['email_tutor'] = request.form['email_tutor']

        #Check whether the fields are filled
        if '' in data.values():
            return 'Los campos no pueden estar vacíos'
        elif not data['phone'].isdigit():
            return 'El campo teléfono solo debe contener dígitos'
        elif not data['enrollment'].isdigit():
            return 'El campo matrícula solo debe contener dígitos'
        else:
            try:
                cur.execute(f''' SELECT NombreAlum FROM alumno WHERE MatAlum= '{data['enrollment']}' ''')
                user = cur.fetchall()
            except:
                return 'Hubo un problema al guadar la información en la base de datos'

            if user:
                return 'Ya existe un usuario registrado con esa matrícula'

            try:
                cur.execute(f''' SELECT CveCarrera FROM carreras WHERE DescripcionCarrera = '{data['career']}' ''')
                data['career'] = cur.fetchall()[0][0]
            except:
                return 'Hubo un problema al obtener la información de la base de datos'

            data['password'] = generate_password_hash(data['password'], method = 'sha256')

            try:
                cur.execute(f'''INSERT INTO alumno VALUES({data['enrollment']}, '{data['name']}', '{data['first_last_name']}', '{data['second_last_name']}', {data['career']}, {data['semester']}, '{data['email']}', '{data['phone']}', '{data['gender']}', '{data['password']}', '{data['name_tutor']}', '{data['first_last_name_tutor']}', '{data['second_last_name_tutor']}', '{data['phone_tutor']}', '{data['email_tutor']}', 2)''')
            except:
                return 'Hubo un problema al guadar la información en la base de datos'

            mysql.connection.commit()

            #Implement message of success instead
            return 'Alumno registrado con éxito'

    try:
        cur.execute(''' SELECT * FROM carreras''')
        r_career = cur.fetchall()
    except:
        return 'Hubo un problema al obtener la información de la base de datos'


    return render_template('admin/students_subscribe.html', active = 'admin_students', r_career = r_career)
    #FIN
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

@app.route('/alumno')
@app.route('/alumno/')
@app.route('/alumno/inicio')
@requires_access_level_and_session(roles['student'])
def student_home():
    try:
        cur.execute(f'''SELECT NombreAlum FROM alumno WHERE MatAlum = '{session['user']}' ''')
        student_name = cur.fetchall()[0][0]
    except:
        return 'Hubo un problema al obtener la información de la base de datos'

    return render_template('student/home.html', active = 'student_home', student_name = student_name)

@app.route('/alumno/agenda')
@requires_access_level_and_session(roles['student'])
def student_schedule():
    return render_template('student/schedule.html', active = 'student_schedule')

@app.route('/alumno/datos')
@requires_access_level_and_session(roles['student'])
def student_data():
    try:
        cur.execute(f'''SELECT NombreAlum, Primer_ApellidoA, Segundo_ApellidoA, DescripcionCarrera, Semestre, CorreoAlum, TelAlum, SexoA, NombreTutor, Primer_ApellidoT, Segundo_ApellidoT, TelTutor, CorreoTutor FROM alumno INNER JOIN carreras ON alumno.Carrera = carreras.CveCarrera WHERE MatAlum = {session['user']} ''')
        student_data = cur.fetchall()
    except:
        return 'Hubo un problema al guadar la información en la base de datos'

    return render_template('student/data.html', active = 'student_data', student_data = student_data)

if __name__ == '__main__':
    app.run(debug = True)

