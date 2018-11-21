from flask import Flask, render_template, session, request
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
    return render_template('index.html')

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
        print(puesto)
        cur.execute(f'''SELECT cve_puesto FROM puesto WHERE desc_puesto = '{puesto}' ''')
        puesto = cur.fetchall()[0][0]
        print("#############################################################")
        print(puesto)
        print("#############################################################")
        horaEntrada = request.form['horaEntrada']
        horaSalida = request.form['horaSalida']
        lugar = request.form['lugar']
        print(lugar)
        cur.execute(f'''SELECT CveLugar FROM lugar WHERE DescLugar = '{lugar}' ''')
        lugar = cur.fetchall()[0][0]
        print("#############################################################")
        print(lugar)
        print("#############################################################")
        sistema = request.form['sistema']
        print(sistema)
        cur.execute(f'''SELECT cve_sistema FROM sistema WHERE esta = {sistema} ''')
        sistema =  cur.fetchall()[0][0]
        print("#############################################################")
        print(sistema)
        print("#############################################################")
        contraseña = request.form['contraseña']

        cur.execute(f'''INSERT INTO profesionista VALUES('{rfc}', '{nombre}', '{apellidoMaterno}', '{apellidoPaterno}', '{correo}', '{telefono}', '{rfc}', {puesto}, '{contraseña}', '{horaEntrada}', '{horaSalida}', {lugar}, {sistema})''')
        mysql.connection.commit()
        cur.close()

        #cur.execute('''SELECT * FROM profesionista''')
        #result_prof = cur.fetch_all()
        return 'Done!'
        #return result_prof



    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM lugar''')
    #use mysql.connection.commit()
    #if you are making an insert into the table (you need to tell mysql objecto to commit that query)
    r_lugar = cur.fetchall()
    cur.execute('''SELECT * FROM puesto''')
    r_puesto = cur.fetchall()
    cur.execute('''SELECT * FROM sistema''')
    r_sistema = cur.fetchall()
    cur.close()
    return render_template('admin_professionals_subscribe.html', active = 'admin_professionals', r_lugar = r_lugar, r_puesto = r_puesto, r_sistema = r_sistema)

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


#cur = mysql.connection.cursor()
#cur.execute('''SELECT * FROM profesionista''')
##use mysql.connection.commit()
##if you are making an insert into the table (you need to tell mysql objecto to commit that query)
#rv = cur.fetchall()
#cur.close()
#return str(rv[0][1])
