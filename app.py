from flask import Flask, render_template, redirect, url_for, request, session, flash
from datetime import datetime, timedelta
import random

app = Flask(__name__)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=36500) 
app.secret_key = 'your_secret_key'  # Change this to a secure secret key

# Hardcoded credentials
USERNAME = 'user'
PASSWORD = 'password'

# List of punishments
punishments = [
    "No access to the app for 1 day",
    "Must write a 500-word essay on time management",
    "No entertainment (TV, games, etc.) for 1 day",
    "Must complete a household chore assigned by an admin",
    "No social media for 1 day"
]

# Initialize user points and other variables
user_data = {
    'points': 25,
    'last_reset': datetime.now(),
    'daily_decrement': 0,
    'punished': False,
    'punishment_end': datetime.now(),
    'current_punishment': ""
}

def reset_points():
    user_data['points'] = 25
    user_data['last_reset'] = datetime.now()
    user_data['daily_decrement'] = 0
    user_data['punished'] = False
    user_data['punishment_end'] = datetime.now()
    user_data['current_punishment'] = ""

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            reset_points()
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid Credentials. Please try again.')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    now = datetime.now()
    # Reset points if a week has passed since the last reset
    if now - user_data['last_reset'] > timedelta(weeks=1):
        reset_points()

    # End punishment if the punishment period has passed
    if user_data['punished'] and now >= user_data['punishment_end']:
        user_data['punished'] = False
        user_data['points'] = 25  # Restore points after punishment ends
        user_data['current_punishment'] = ""

    return render_template('dashboard.html', points=user_data['points'], punished=user_data['punished'], punishment=user_data['current_punishment'], punishment_end=user_data['punishment_end'])

@app.route('/decrement', methods=['POST'])
def decrement_points():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    if user_data['punished']:
        flash('You are currently under punishment.')
        return redirect(url_for('dashboard'))
    
    now = datetime.now()
    decrement_amount = int(request.form['decrement'])
    if decrement_amount <= 0 or decrement_amount > user_data['points']:
        flash('Invalid decrement amount.')
        return redirect(url_for('dashboard'))
    
    # Check daily decrement limit
    if (now - user_data['last_reset']).days < 1:
        if user_data['daily_decrement'] + decrement_amount > 5:
            flash('You cannot decrease more than 5 points in a single day.')
            return redirect(url_for('dashboard'))
        user_data['daily_decrement'] += decrement_amount
    else:
        user_data['daily_decrement'] = decrement_amount

    user_data['points'] -= decrement_amount

    # Check for punishable behavior: Weekly exhaustion has priority
    if user_data['points'] <= 0:
        user_data['punished'] = True
        user_data['punishment_end'] = now + timedelta(days=1)
        user_data['current_punishment'] = "Points exhausted. No access to the app for 1 day."
        flash('You have been punished for exhausting your points. Points will be restored after the punishment period. ' + user_data['current_punishment'])
    elif decrement_amount >= 5:
        user_data['punished'] = True
        user_data['punishment_end'] = now + timedelta(days=1)
        user_data['current_punishment'] = random.choice(punishments)
        flash('You have been punished for decrementing more than 5 points in a single day. ' + user_data['current_punishment'])

    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
