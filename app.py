from flask import Flask, render_template, session, request, redirect, url_for, jsonify
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
app.config['MYSQL_DB'] = 'sacda'

mysql = MySQL(app)
mail = Mail(app)
cur = None #This global variable (cursor) makes it posible to open/close database connection with before_request/after_request decorators
roles = { 'student' : 1, 'professional' : 2, 'admin' : 3}
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

def requires_access_level_and_session(access_level):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session:
                return redirect(url_for('login'))

            try:
                cur.execute(f''' SELECT rol FROM profesionista WHERE id = '{session['user']}' ''')
                professional = cur.fetchall()

                cur.execute(f''' SELECT rol FROM administrador WHERE id = '{session['user']}' ''')
                admin = cur.fetchall()

                cur.execute(f''' SELECT rol FROM estudiante WHERE id = '{session['user']}' ''')
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
            cur.execute(f''' SELECT correo, nombre FROM profesionista WHERE id = '{user}' ''')
            professional = cur.fetchall()

            cur.execute(f''' SELECT correo, nombre FROM administrador WHERE id = '{user}' ''')
            admin = cur.fetchall()

            cur.execute(f''' SELECT correo, nombre FROM estudiante WHERE id = '{user}' ''')
            student = cur.fetchall()

            if professional:
                user_mail = professional[0][0]
                user_name = professional[0][1]
                user_identifier_field = 'id'
                user_role_field = 'profesionista'
                user_password_field = 'contraseña'
            elif admin:
                user_mail = admin[0][0]
                user_name = admin[0][1]
                user_identifier_field = 'id'
                user_role_field = 'administrador'
                user_password_field = 'contraseña'
            elif student:
                user_mail = student[0][0]
                user_name = student[0][1]
                user_identifier_field = 'id'
                user_role_field = 'estudiante'
                user_password_field = 'contraseña'
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
@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = {}
        data['user'] = request.form['user']
        data['password'] = request.form['password']
        redirect_user = None
        in_system = False

        if '' in data.values():
            return jsonify({'error':'Los campos no pueden estar vacíos'})

        try:
            cur.execute(f''' SELECT contraseña, sistema FROM profesionista WHERE id = '{data['user']}' ''')
            professional = cur.fetchall()

            cur.execute(f''' SELECT contraseña FROM administrador WHERE id = '{data['user']}' ''')
            admin = cur.fetchall()

            cur.execute(f''' SELECT contraseña, sistema FROM estudiante WHERE id = '{data['user']}' ''')
            student = cur.fetchall()

            if professional:
                redirect_user = 'professional_home'
                r_password = professional[0][0]
                if professional[0][1] == 1:
                    in_system = True
            elif admin:
                redirect_user = 'admin_home'
                r_password = admin[0][0]
                in_system = True
            elif student:
                redirect_user = 'student_home'
                r_password = student[0][0]
                if student[0][1] == 1:
                    in_system = True
            else:
                return jsonify({'error':'La contraseña o el usuario son incorrectos'})
        except:
            return jsonify({'error':'Hubo un problema al obtener la información de la base de datos'})

        #Checking if the password given is correct and is a registered user
        #TODO: add "in system" flags to student and admin
        if check_password_hash(r_password, data['password']) and in_system:
            session['user'] = data['user']
            return jsonify({'new_url' : url_for(redirect_user) })

        return jsonify({'error':'La contraseña o el usuario son incorrectos'})

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
            return jsonify({'error':'Los campos no pueden estar vacíos'})
        elif not data['phone'].isdigit():
            return jsonify({'error':'El campo teléfono debe contener únicamente números'})
        else:
            try:
                cur.execute(f''' SELECT nombre FROM profesionista WHERE id= '{data['rfc']}' ''')
                user = cur.fetchall()
            except:
                return jsonify({'error':'Hubo un error al obtener información de la base de datos'})
            if user:
                return jsonify({'error':'Ya existe un usuario con este RFC'})

            try:
                cur.execute(f''' SELECT id FROM puesto WHERE descripcion = '{data['job']}' ''')
                data['job'] = cur.fetchall()[0][0]

                cur.execute(f''' SELECT id FROM lugar WHERE descripcion = '{data['place']}' ''')
                data['place'] = cur.fetchall()[0][0]
            except:
                return jsonify({'error':'Hubo un error al obtener información de la base de datos'})

            data['password'] = generate_password_hash(data['password'], method = 'sha256')

            try:
                cur.execute(f'''
                            INSERT into profesionista (id, nombre, primer_apellido, segundo_apellido, correo, telefono, puesto, contraseña, lugar)
                            values
                            ('{data['rfc']}', '{data['name']}', '{data['first_last_name']}', '{data['second_last_name']}', '{data['email']}', '{data['phone']}', {data['job']}, '{data['password']}', {data['place']})
                             ''')

                cur.execute(f'''
                            INSERT INTO horario
                            VALUES
                            ('{data['rfc']}', '{data['entry_time']}', '{data['exit_time']}', '{data['entry_time']}', '{data['exit_time']}', '{data['entry_time']}', '{data['exit_time']}', '{data['entry_time']}', '{data['exit_time']}', '{data['entry_time']}', '{data['exit_time']}')
                             ''')
            except:
                return jsonify({'error':'Hubo un error al insertar información en la base de datos'})

            mysql.connection.commit()

            #Implement message of success instead
            return jsonify({'new_url' : url_for('admin_professionals_subscribe'), 'success' : 'El profesionista se añadió correctamente' })

    try:
        cur.execute(''' SELECT * FROM lugar''')
        r_place = cur.fetchall()

        cur.execute(''' SELECT * FROM puesto''')
        r_job = cur.fetchall()
    except:
        return jsonify({'error':'Hubo un error al obtener información de la base de datos'})


    return render_template('admin/professionals_subscribe.html', active = 'admin_professionals', r_place = r_place, r_job = r_job)

@app.route('/administrador/profesionales/baja', methods = ['GET', 'POST'])
@requires_access_level_and_session(roles['admin'])
def admin_professionals_unsubscribe():
    if request.method == 'POST':
        professional_key = request.form['to_delete']

        try:
            cur.execute(f''' UPDATE profesionista SET sistema = 0 WHERE id = '{professional_key}' ''')
        except:
            return 'Hubo un problema al actualizar la información en la base de datos'

        mysql.connection.commit()

        return redirect(url_for('admin_professionals_unsubscribe'))

    try:
        cur.execute(f'''
                    SELECT profesionista.id, nombre, primer_apellido, segundo_apellido, puesto.descripcion, lugar.descripcion FROM profesionista INNER JOIN puesto on profesionista.puesto = puesto.id INNER JOIN lugar ON profesionista.lugar = lugar.id WHERE sistema = 1
                    ''')
        r_professionals = cur.fetchall()
    except:
        return 'Hubo un problema al obtener la información de la base de datos'

    return render_template('admin/professionals_unsubscribe.html', active = 'admin_professionals', r_professionals = r_professionals)

@app.route('/administrador/profesionales/modificar', methods = ['GET', 'POST'])
@requires_access_level_and_session(roles['admin'])
def admin_professionals_modify():
    if request.method == 'POST':
        professional_key = request.form['to_select']

        return redirect(url_for('admin_professionals_modify_commit', professional_key = professional_key))

    try:
        cur.execute(f''' SELECT profesionista.id, nombre, primer_apellido, segundo_apellido, puesto.descripcion, lugar.descripcion, horario.lunes_entrada,horario.lunes_salida, correo, telefono FROM profesionista INNER JOIN puesto ON profesionista.puesto = puesto.id INNER JOIN lugar ON profesionista.lugar = lugar.id INNER JOIN horario ON profesionista.id = horario.id  WHERE sistema = 1''')
        r_professionals = cur.fetchall()
    except:
        return 'Hubo un problema al obtener la información de la base de datos'

    return render_template('admin/professionals_modify.html', active = 'admin_professionals', r_professionals = r_professionals)

@app.route('/administrador/profesionales/ver', methods = ['GET', 'POST'])
@requires_access_level_and_session(roles['admin'])
def admin_professionals_data():
    if request.method == 'POST':
        professional_key = request.form['to_select']

        return redirect(url_for('admin_professionals_horario', professional_key = professional_key))

    try:
        cur.execute(f''' SELECT profesionista.id, nombre, primer_apellido, segundo_apellido, puesto.descripcion, lugar.descripcion, horario.lunes_entrada,horario.lunes_salida, correo, telefono FROM profesionista INNER JOIN puesto ON profesionista.puesto = puesto.id INNER JOIN lugar ON profesionista.lugar = lugar.id INNER JOIN horario ON profesionista.id = horario.id  WHERE sistema = 1''')
        r_professionals = cur.fetchall()
    except:
        return 'Hubo un problema al obtener la información de la base de datos'

    return render_template('admin/professionals_data.html', active = 'admin_professionals', r_professionals = r_professionals)

@app.route('/administrador/profesionales/ver/horario', methods = ['GET', 'POST'])
@requires_access_level_and_session(roles['admin'])
def admin_professionals_horario():
    if request.method == 'POST':
        professional_key = request.form['to_select']

        return redirect(url_for('admin_professionals_horario', professional_key = professional_key))

    try:
        cur.execute(f''' SELECT nombre, primer_apellido, segundo_apellido, horario.lunes_entrada, horario.lunes_salida, horario.martes_entrada, horario.martes_salida, horario.miercoles_entrada, horario.miercoles_salida, horario.jueves_entrada, horario.jueves_salida, horario.viernes_entrada, horario.viernes_salida FROM profesionista INNER JOIN puesto ON profesionista.puesto = puesto.id INNER JOIN lugar ON profesionista.lugar = lugar.id INNER JOIN horario ON profesionista.id = horario.id WHERE sistema = 1 ''')
        r_professionals = cur.fetchall()
    except:
        return 'Hubo un problema al obtener la información de la base de datos'

    return render_template('admin/professionals_horarios.html', active = 'admin_professionals', r_professionals = r_professionals)

@app.route('/administrador/profesionales/modificar/editar', methods = ['GET', 'POST'])
@requires_access_level_and_session(roles['admin'])
def admin_professionals_modify_commit():
    professional_key =  request.args.get('professional_key')
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

        #Check whether the fields are filled
        if '' in data.values():
            return 'Los campos no puedes estar vacíos'
        elif not data['phone'].isdigit():
            return 'El campo teléfono debe contener unicamente números'
        else:
            try:
                cur.execute(f'''
                            UPDATE horario SET lunes_entrada = '{data['entry_time']}', lunes_salida = '{data['exit_time']}', martes_entrada = '{data['entry_time']}', martes_salida = '{data['exit_time']}', miercoles_entrada = '{data['entry_time']}', miercoles_salida = '{data['exit_time']}', jueves_entrada = '{data['entry_time']}', jueves_salida = '{data['exit_time']}', viernes_entrada = '{data['entry_time']}', viernes_salida = '{data['exit_time']}' WHERE id = '{data['rfc']}';
                        ''')

                cur.execute(f''' UPDATE profesionista SET nombre = '{data['name']}', primer_apellido = '{data['first_last_name']}', segundo_apellido = '{data['second_last_name']}', correo = '{data['email']}', telefono = '{data['phone']}', puesto = {data['job']}, lugar = {data['place']} WHERE id = '{data['rfc']}' ''')
            except:
                return 'Hubo un problema al actualizar la información de la base de datos'

            mysql.connection.commit()
            return redirect(url_for('admin_professionals_modify'))

    try:
        cur.execute(f''' SELECT * FROM lugar ''')
        r_place = cur.fetchall()

        cur.execute(f''' SELECT * FROM puesto''')
        r_job = cur.fetchall()

        cur.execute(f''' SELECT id, lunes_entrada, lunes_salida FROM horario WHERE id = {professional_key} ''')
        r_schedule = cur.fetchall()

        cur.execute(f'''
                    SELECT profesionista.id, correo, telefono, nombre, primer_apellido, segundo_apellido, puesto.descripcion, horario.lunes_entrada, horario.lunes_salida, lugar.descripcion from profesionista INNER JOIN puesto ON profesionista.puesto = puesto.id INNER JOIN lugar ON profesionista.lugar = lugar.id INNER JOIN horario ON horario.id = profesionista.id WHERE profesionista.id = '{professional_key}' AND sistema = 1
                ''')
        professional = cur.fetchall()
    except:
        return 'Hubo un problema al obtener la información de la base de datos'

    return render_template('admin/professionals_modify_commit.html', active = 'admin_professionals', r_place = r_place, r_job = r_job, r_schedule = r_schedule,  professional = professional)

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
            #return 'Los campos no pueden estar vacíos'
            return render_template('admin/students_subscribe.html', sent = 0)
        elif not data['phone'].isdigit():
            #return 'El campo teléfono solo debe contener dígitos'
            return render_template('admin/students_subscribe.html', sent = 1)
        elif not data['enrollment'].isdigit():
            #return 'El campo matrícula solo debe contener dígitos'
            return render_template('admin/students_subscribe.html', sent = 2)
        else:
            try:
                cur.execute(f''' SELECT nombre FROM estudiante WHERE id = '{data['enrollment']}' ''')
                user = cur.fetchall()
            except:
                #return 'Hubo un problema al guadar la información en la base de datos'
                return render_template('admin/students_subscribe.html', sent = 3)
            if user:
                #return 'Ya existe un usuario registrado con esa matrícula'
                return render_template('admin/students_subscribe.html', sent = 4)

            try:
                cur.execute(f''' SELECT id FROM carrera WHERE descripcion = '{data['career']}' ''')
                data['career'] = cur.fetchall()[0][0]
            except:
                #return 'Hubo un problema al obtener la información de la base de datos'
                return render_template('admin/students_subscribe.html', sent = 5)

            data['password'] = generate_password_hash(data['password'], method = 'sha256')

            try:
                cur.execute(f'''
                            INSERT INTO estudiante (id, nombre, primer_apellido, segundo_apellido, carrera, semestre, correo, telefono, genero, contraseña, nombre_tutor, primer_apellido_tutor, segundo_apellido_tutor, telefono_tutor, correo_tutor) VALUES('{data['enrollment']}', '{data['name']}', '{data['first_last_name']}', '{data['second_last_name']}', {data['career']}, {data['semester']}, '{data['email']}', '{data['phone']}', '{data['gender']}', '{data['password']}', '{data['name_tutor']}', '{data['first_last_name_tutor']}', '{data['second_last_name_tutor']}', '{data['phone_tutor']}', '{data['email_tutor']}')
                            ''')
            except:
                #return 'Hubo un problema al obtener la información de la base de datos'
                return render_template('admin/students_subscribe.html', sent = 5)

            mysql.connection.commit()

            #Implement message of success instead
            return render_template('admin/students_subscribe.html', sent = 6)


    try:
        cur.execute(''' SELECT * FROM carrera''')
        r_career = cur.fetchall()
    except:
        #Error con la base
        return render_template('admin/students_subscribe.html', sent = 5)


    return render_template('admin/students_subscribe.html', active = 'admin_students', r_career = r_career, sent = 'unknown')

@app.route('/administrador/estudiantes/modificar',  methods = ['GET','POST'])
@requires_access_level_and_session(roles['admin'])
def admin_students_modify():
    if request.method == 'POST':
        student_key = request.form['to_select']
        return redirect(url_for('admin_students_modify_commit', student_key = student_key))

    try:
        cur.execute(f''' SELECT estudiante.id, nombre, primer_apellido, segundo_apellido, carrera.descripcion, semestre, correo, telefono FROM estudiante INNER JOIN  carrera ON carrera.id = estudiante.carrera WHERE Sistema = 1''')
        r_students = cur.fetchall()
    except:
        return 'Hubo un problema al obtener la información de la base de datos'

    return render_template('admin/students_modify.html', active = 'admin_students', r_students = r_students)

@app.route('/administrador/estudiantes/modificar/editardatos', methods = ['GET', 'POST'])
@requires_access_level_and_session(roles['admin'])
def admin_students_modify_commit():
    student_key =  request.args.get('student_key')
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
        #Tutor
        data['name_tutor'] = request.form['name_tutor']
        data['first_last_name_tutor'] = request.form['first_last_name_tutor']
        data['second_last_name_tutor'] = request.form['second_last_name_tutor']
        data['phone_tutor'] = request.form['phone_tutor']
        data['email_tutor'] = request.form['email_tutor']

        #Check whether the fields are filled
        if '' in data.values():
            return 'Los campos no puedes estar vacíos'
        elif not data['phone'].isdigit():
            return 'El campo teléfono debe contener unicamente números'
        else:
            try:
                cur.execute(f''' UPDATE estudiante SET nombre = '{data['name']}', primer_apellido = '{data['first_last_name']}', segundo_apellido = '{data['second_last_name']}', correo = '{data['email']}', telefono = '{data['phone']}', carrera = {data['career']}, semestre = {data['semester']}, nombre_tutor = '{data['name_tutor']}', primer_apellido_tutor = '{data['first_last_name_tutor']}', segundo_apellido_tutor = '{data['second_last_name_tutor']}', telefono_tutor = '{data['phone_tutor']}', correo_tutor = '{data['email_tutor']}', genero = '{data['gender']}' WHERE id = {data['enrollment']} ''')
            except:
                return 'Hubo un problema al actualizar la información de la base de datos'

            mysql.connection.commit()
            return redirect(url_for('admin_students_modify'))

    try:
        cur.execute(f''' SELECT * FROM carrera''')
        r_career = cur.fetchall()

        cur.execute(f'''SELECT estudiante.id, nombre, primer_apellido, segundo_apellido, carrera.descripcion, semestre, correo, telefono, nombre_tutor, primer_apellido_tutor, segundo_apellido_tutor, telefono_tutor, correo_tutor, genero FROM estudiante INNER JOIN carrera ON carrera.id = estudiante.carrera WHERE estudiante.id = '{student_key}' AND sistema = 1''')
        student = cur.fetchall()
    except:
        return 'Hubo un problema al obtener la información de la base de datos modificar commit'

    return render_template('admin/students_modify_commit.html', active = 'admin_students',  student = student, r_career = r_career)

@app.route('/administrador/estudiantes/baja', methods = ['GET', 'POST'])
@requires_access_level_and_session(roles['admin'])
def admin_students_unsubscribe():
    if request.method == 'POST':
        student_key = request.form['to_delete']

        try:
            cur.execute(f''' UPDATE estudiante SET sistema = 0 WHERE id = '{student_key}' ''')
        except:
            return 'Hubo un problema al actualizar la información en la base de datos'

        mysql.connection.commit()

        return redirect(url_for('admin_students_unsubscribe'))

    try:
        cur.execute('''
                    SELECT estudiante.id, nombre, primer_apellido, segundo_apellido, carrera.descripcion, semestre FROM estudiante INNER JOIN carrera on estudiante.carrera = carrera.id WHERE sistema = 1;
                    ''')
        r_students = cur.fetchall()
    except:
        return 'Hubo un problema al obtener la información de la base de datos'

    return render_template('admin/students_unsubscribe.html', active = 'admin_students', r_students = r_students)

@app.route('/administrador/estudiantes/datos', methods = ['GET', 'POST'])
@requires_access_level_and_session(roles['admin'])
def admin_students_data():
    if request.method == 'POST':
        student_key = request.form['to_select']

        return redirect(url_for('admin/student_data_tutor', student_key = student_key))

    try:
        cur.execute(f'''
                    SELECT estudiante.id, nombre, primer_apellido, segundo_apellido, carrera.descripcion, semestre, correo, telefono, genero, faltas FROM estudiante INNER JOIN carrera on estudiante.carrera = carrera.id WHERE sistema = 1;
                    ''')
        r_students = cur.fetchall()
    except:
        return 'Hubo un problema al obtener la información de la base de datos'

    return render_template('admin/students_data.html', active = 'admin_students', r_students = r_students)

@app.route('/administrador/estudiantes/datos/tutor', methods = ['GET', 'POST'])
@requires_access_level_and_session(roles['admin'])
def admin_students_data_tutor():
    try:
        cur.execute(f'''
                    SELECT estudiante.id, nombre_tutor, primer_apellido_tutor, segundo_apellido_tutor, correo_tutor, telefono_tutor FROM estudiante INNER JOIN carrera on estudiante.carrera = carrera.id WHERE sistema = 1;
                    ''')
        r_students = cur.fetchall()
    except:
        return 'Hubo un problema al obtener la información de la base de datos'

    return render_template('admin/students_data_tutor.html', active = 'admin_students', r_students = r_students)


@app.route('/administrador/agendas')
@requires_access_level_and_session(roles['admin'])
def admin_schedule():
    return render_template('admin/schedule.html', active = 'admin_schedule')

@app.route('/administrador/estadisticas/generales', methods = ['GET', 'POST'])
@requires_access_level_and_session(roles['admin'])
def admin_statistics_general():
    if request.method == 'POST':
        data = {}

        data['start_date'] = request.form['start_date']
        data['finish_date'] = request.form['finish_date']
        data['career'] = request.form['career']
        data['service'] = request.form['service']

        try:
            cur.execute(f'''
                    SELECT * FROM cita INNER JOIN estudiante ON cita.id_estudiante = estudiante.id INNER JOIN profesionista ON cita.id_profesionista = profesionista.id WHERE estudiante.carrera = (SELECT carrera.id FROM carrera WHERE carrera.descripcion = '{data['career']}') AND profesionista.puesto = (SELECT puesto.id FROM puesto WHERE puesto.descripcion = '{data['service']}') AND cita.fecha BETWEEN '{data['start_date']}' AND '{data['finish_date']}'
                        ''')
            query_data = cur.fetchall()
        except:
            return 'Hubo un problema al obtener la información de la base de datos'

        return render_template('admin/statistics_general_view.html', active = 'admin_statistics_general', query_data = query_data)
        #return str(query_data)

    try:
        cur.execute(''' SELECT * FROM carrera''')
        r_career = cur.fetchall()
        cur.execute(''' SELECT * FROM puesto''')
        r_service = cur.fetchall()
    except:
        return 'Hubo un problema al obtener la información de la base de datos'

    return render_template('admin/statistics_general.html', active = 'admin_statistics', r_service = r_service, r_career = r_career)

@app.route('/administrador/estadisticas/profesionistas/vista', methods = ['GET','POST'])
@requires_access_level_and_session(roles['admin'])
def statics_general_view():
    pass

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
        cur.execute(f'''SELECT nombre FROM profesionista WHERE id = '{session['user']}' ''')
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
        cur.execute(f'''
                    SELECT nombre, primer_apellido, segundo_apellido, correo, telefono, puesto.descripcion, horario.lunes_entrada, horario.lunes_salida, lugar.descripcion FROM profesionista INNER JOIN puesto ON profesionista.puesto = puesto.id INNER JOIN horario ON profesionista.id = horario.id INNER JOIN lugar ON profesionista.lugar = lugar.id WHERE profesionista.id = '{session['user']}'
                    ''')
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
        cur.execute(f'''SELECT nombre FROM estudiante WHERE id = '{session['user']}' ''')
        student_name = cur.fetchall()[0][0]
    except:
        return 'Hubo un problema al obtener la información de la base de datos'

    return render_template('student/home.html', active = 'student_home', student_name = student_name)

@app.route('/alumno/agendar')
@requires_access_level_and_session(roles['student'])
def student_schedule():
    return render_template('student/schedule.html', active = 'student_schedule')

@app.route('/alumno/datos/modificar', methods = ['GET','POST'])
@requires_access_level_and_session(roles['student'])
def student_modify():
    student_key =  request.args.get('student_key')
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
        #Tutor
        data['name_tutor'] = request.form['name_tutor']
        data['first_last_name_tutor'] = request.form['first_last_name_tutor']
        data['second_last_name_tutor'] = request.form['second_last_name_tutor']
        data['phone_tutor'] = request.form['phone_tutor']
        data['email_tutor'] = request.form['email_tutor']

        #Check whether the fields are filled
        if '' in data.values():
            return 'Los campos no puedes estar vacíos'
        elif not data['phone'].isdigit():
            return 'El campo teléfono debe contener unicamente números'
        else:
            try:
                cur.execute(f''' UPDATE estudiante SET nombre = '{data['name']}', primer_apellido = '{data['first_last_name']}', segundo_apellido = '{data['second_last_name']}', correo = '{data['email']}', telefono = '{data['phone']}', carrera = {data['career']}, semestre = {data['semester']}, nombre_tutor = '{data['name_tutor']}', primer_apellido_tutor = '{data['first_last_name_tutor']}', segundo_apellido_tutor = '{data['second_last_name_tutor']}', telefono_tutor = '{data['phone_tutor']}', correo_tutor = '{data['email_tutor']}', genero = '{data['gender']}' WHERE id = {data['enrollment']} ''')
            except:
                return 'Hubo un problema al actualizar la información de la base de datos'

            mysql.connection.commit()
            return redirect(url_for('student_data'))

    try:
        cur.execute(f''' SELECT * FROM carrera''')
        r_career = cur.fetchall()

        cur.execute(f'''SELECT estudiante.id, nombre, primer_apellido, segundo_apellido, carrera.descripcion, semestre, correo, telefono, nombre_tutor, primer_apellido_tutor, segundo_apellido_tutor, telefono_tutor, correo_tutor, genero FROM estudiante INNER JOIN carrera ON carrera.id = estudiante.carrera WHERE estudiante.id = {student_key} AND sistema = 1''')
        student = cur.fetchall()
    except:
        return 'Hubo un problema al obtener la información de la base de datos modificar commit'

    return render_template('student/modify.html', active = 'student_data', student = student, r_career = r_career)

@app.route('/alumno/datos', methods = ['GET','POST'])
@requires_access_level_and_session(roles['student'])
def student_data():
    if request.method == 'POST':
        student_key = request.form['to_select']
        return redirect(url_for('student_modify', student_key = student_key ))
   
    try:
        cur.execute(f''' SELECT nombre, primer_apellido, segundo_apellido, carrera.descripcion, semestre, correo, telefono, genero, nombre_tutor, primer_apellido_tutor, segundo_apellido_tutor, telefono_tutor, correo_tutor, estudiante.id FROM estudiante INNER JOIN carrera on estudiante.carrera = carrera.id WHERE estudiante.id = '{session['user']}' ''')
        student_data = cur.fetchall()
    except:
        return 'Hubo un problema al obtener la información en la base de datos'

    return render_template('student/data.html', active = 'student_data', student_data = student_data)

@app.route('/alumno/citas', methods = ['GET','POST'])
@requires_access_level_and_session(roles['student'])
def student_appointment():
    if request.method == 'POST':
        appointment_key = request.form['to_delete']

        try:
            cur.execute(f''' UPDATE cita SET sistema = 0 WHERE id = '{appointment_key}' ''')
        except:
            return 'Hubo un problema en actualizar la información en la base de datos'

        mysql.connection.commit()
        return redirect(url_for('student_appointment'))

    try:
        cur.execute(f''' SELECT cita.id, profesionista.nombre, profesionista.primer_apellido,fecha, hora_inicio, hora_fin, puesto.descripcion, lugar.descripcion FROM cita INNER JOIN profesionista ON cita.id_profesionista = profesionista.id INNER JOIN puesto ON profesionista.puesto = puesto.id INNER JOIN lugar ON profesionista.lugar = lugar.id WHERE cita.id_estudiante = '{session['user']}' AND cita.sistema = 1 ''')
        r_appointments = cur.fetchall()
    except:
        return 'Hubo un problema al obtener la información de la base de datos citas'

    return render_template('student/appointment.html', active = 'student_appointment', r_appointments = r_appointments)

if __name__ == '__main__':
    app.run(debug = True)

