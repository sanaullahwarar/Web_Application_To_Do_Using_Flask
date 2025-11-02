from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Task
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home/Login Page
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid email or password', 'danger')
    return render_template('index.html')

# Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'warning')
            return redirect(url_for('register'))
        new_user = User(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.due_date.asc()).all()
    return render_template('dashboard.html', tasks=tasks)

# Add Task
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_task():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        due_date = request.form['due_date']
        priority = request.form['priority']
        category = request.form['category']
        new_task = Task(
            title=title, description=description, due_date=due_date,
            priority=priority, category=category, user_id=current_user.id
        )
        db.session.add(new_task)
        db.session.commit()
        flash('Task added successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_task.html')

# Edit Task
@app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash("You can't edit this task!", 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        task.title = request.form['title']
        task.description = request.form['description']
        task.due_date = request.form['due_date']
        task.priority = request.form['priority']
        task.category = request.form['category']
        db.session.commit()
        flash('Task updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('edit_task.html', task=task)

# Delete Task
@app.route('/delete/<int:task_id>')
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id == current_user.id:
        db.session.delete(task)
        db.session.commit()
        flash('Task deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

# Mark Complete
@app.route('/complete/<int:task_id>')
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id == current_user.id:
        task.is_completed = not task.is_completed
        db.session.commit()
    return redirect(url_for('dashboard'))

# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
