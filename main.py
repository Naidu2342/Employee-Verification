from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'

EMPLOYEE_FILE = 'employees.csv'

# Sample login credentials
users = {
    "admin": "Hackculprit"
}

# Load employee data
def load_employees():
    return pd.read_csv(EMPLOYEE_FILE)

def save_employees(df):
    df.to_csv(EMPLOYEE_FILE, index=False)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid username or password")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/lookup', methods=['POST'])
def lookup():
    if 'username' not in session:
        return {'status': 'error', 'message': 'Unauthorized'}, 401

    data = request.get_json()
    emp_id = data.get('id', '').strip()
    df = load_employees()
    emp = df[df['id'] == emp_id]
    if not emp.empty:
        emp_data = emp.iloc[0].to_dict()
        return {'status': 'success', 'employee': emp_data}
    else:
        return {'status': 'error', 'message': f'Employee ID "{emp_id}" not found.'}

@app.route('/employees')
def employees():
    if 'username' not in session:
        return redirect(url_for('login'))
    df = load_employees()
    return render_template('employees.html', employees=df.to_dict(orient='records'))

@app.route('/add_employee', methods=['POST'])
def add_employee():
    if 'username' not in session:
        return redirect(url_for('login'))

    emp_id = request.form['id']
    name = request.form['name']
    department = request.form['department']
    status = request.form['status']

    df = load_employees()
    if emp_id in df['id'].values:
        return "Employee ID already exists.", 400

    new_row = pd.DataFrame([{
        'id': emp_id,
        'name': name,
        'department': department,
        'status': status
    }])

    df = pd.concat([df, new_row], ignore_index=True)
    save_employees(df)
    return redirect(url_for('employees'))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
