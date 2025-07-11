from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Google Sheets API setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Load credentials from environment variable (for Render)
creds_dict = json.loads(os.environ.get('GOOGLE_CREDS'))
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("Employee").sheet1  # Change "YourSheetName" to your actual Google Sheet name

# Sample login credentials
users = {
    "admin": "Hackculprit"
}

def get_all_employees():
    """Fetch all employee records from Google Sheet as list of dicts."""
    return sheet.get_all_records()

def employee_exists(emp_id):
    """Check if employee id exists."""
    records = get_all_employees()
    return any(emp['id'] == emp_id for emp in records)

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
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    data = request.get_json()
    emp_id = data.get('id', '').strip()
    records = get_all_employees()
    emp = next((emp for emp in records if emp['id'] == emp_id), None)
    if emp:
        return jsonify({'status': 'success', 'employee': emp})
    else:
        return jsonify({'status': 'error', 'message': f'Employee ID "{emp_id}" not found.'})

@app.route('/employees')
def employees():
    if 'username' not in session:
        return redirect(url_for('login'))
    records = get_all_employees()
    return render_template('employees.html', employees=records)

@app.route('/add_employee', methods=['POST'])
def add_employee():
    if 'username' not in session:
        return redirect(url_for('login'))

    emp_id = request.form['id'].strip()
    name = request.form['name'].strip()
    department = request.form['department'].strip()
    status = request.form['status'].strip()

    if employee_exists(emp_id):
        return "Employee ID already exists.", 400

    # Append new row (order should match your sheet columns)
    sheet.append_row([emp_id, name, department, status])

    return redirect(url_for('employees'))

@app.route('/delete_employee/<emp_id>', methods=['POST'])
def delete_employee(emp_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    records = get_all_employees()
    found = False
    for idx, emp in enumerate(records, start=2):
        if emp['id'] == emp_id:
            try:
                sheet.delete_row(idx)
                found = True
                break
            except Exception as e:
                print(f"Error deleting row {idx}: {e}")
                return f"Error deleting employee: {e}", 500

    if not found:
        return f"Employee ID '{emp_id}' not found.", 404

    return redirect(url_for('employees'))



# Optional: Implement delete and update routes similarly using sheet.delete_row() and sheet.update_cell()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
