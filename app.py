from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html', active = 'home')

@app.route('/professionals')
def professionals():
    return render_template('professionals.html', active = 'professionals')

@app.route('/students')
def students():
    return render_template('students.html', active = 'students')

@app.route('/statistics')
def estadistics():
    return render_template('statistics.html', active = 'statistics')

@app.route('/statistics_1')
def statistics_1():
    return render_template('statistics_1.html', active = 'statistics_1')

@app.route('/statistics_2')
def statistics_2():
    return render_template('statistics_2.html', active = 'statistics_2')

if __name__ == '__main__':
    app.run(debug = True)
