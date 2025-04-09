# app.py
from flask import Flask, render_template, redirect, url_for, request, flash, abort,send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db, login_manager
from models import User
import os
from werkzeug.utils import secure_filename
from check_f22_status import process_accounts
import threading
from logger import setup_logger
from check_password import process_accounts as process_accounts_script2
from get_ddjj_table import process_accounts as process_accounts_script3
from get_f29_codes import process_accounts as process_accounts_script4


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

logger = setup_logger()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        abort(403)
    users = User.query.all()
    return render_template('admin.html', users=users)

@app.route('/add_user', methods=['POST'])
@login_required
def add_user():
    if not current_user.is_admin:
        abort(403)
    
    username = request.form.get('username')
    password = request.form.get('password')
    is_admin = 'is_admin' in request.form
    
    if not username or not password:
        flash('Username and password are required', 'danger')
        return redirect(url_for('admin'))
    
    if User.query.filter_by(username=username).first():
        flash('Username already exists', 'danger')
        return redirect(url_for('admin'))
    
    new_user = User(username=username, is_admin=is_admin)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    flash('User created successfully', 'success')
    return redirect(url_for('admin'))

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        abort(403)
    
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash('You cannot delete yourself', 'danger')
        return redirect(url_for('admin'))
    
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully', 'success')
    return redirect(url_for('admin'))

@app.route('/download_output')
@login_required
def download_output():
    files = os.listdir(app.config['OUTPUT_FOLDER'])
    files = sorted([f for f in files if f.endswith('.xlsx')], reverse=True)
    return render_template('download_output.html', files=files)

@app.route('/download/<filename>')
@login_required
def download_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/script1', methods=['POST'])
@login_required
def script1():
    year = request.form.get('year', '2025')
    file = request.files.get('input_file')

    if not file:
        flash('No input file provided.', 'danger')
        logger.warning("No input file uploaded by user: %s", current_user.username)
        return redirect(url_for('dashboard'))

    filename = secure_filename(file.filename)
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(input_path)

    def background_task(input_path, output_dir, year):
        try:
            process_accounts(input_path, output_dir, year)
            logger.info("Script 1 finished successfully.")
        except Exception as e:
            logger.error(f"Error in Script 1 background task: {e}", exc_info=True)

    thread = threading.Thread(target=background_task, args=(input_path, app.config['OUTPUT_FOLDER'], year))
    thread.start()

    flash('Script 1 is running in the background. Check back later to download the output.', 'info')
    return redirect(url_for('dashboard'))


@app.route('/script2', methods=['POST'])
@login_required
def script2():
    file = request.files.get('input_file')
    if not file:
        flash('No input file provided.', 'danger')
        # logger.warning("No input file uploaded for Script 2 by user: %s", current_user.username)
        return redirect(url_for('dashboard'))

    filename = secure_filename(file.filename)
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(input_path)

    def background_task(input_path, output_dir):
        try:
            # logger.info(f"Script 2 started by {username}")
            process_accounts_script2(input_path, output_dir)
            logger.info("Script 2 finished successfully.")
        except Exception as e:
            logger.error(f"Script 2 error: {e}", exc_info=True)

    thread = threading.Thread(target=background_task, args=(input_path, app.config['OUTPUT_FOLDER']))
    thread.start()

    flash('Script 2 is running in the background. Check the output files page shortly.', 'info')
    return redirect(url_for('dashboard'))

@app.route('/script3', methods=['POST'])
@login_required
def script3():
    file = request.files.get('input_file')
    if not file:
        flash('No input file provided.', 'danger')
        logger.warning("No file for Script 3 uploaded by %s", current_user.username)
        return redirect(url_for('dashboard'))

    filename = secure_filename(file.filename)
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(input_path)

    def background_task(input_path, output_dir, username):
        try:
            logger.info(f"Script 3 started by {username}")
            process_accounts_script3(input_path, output_dir)
            logger.info("Script 3 completed.")
        except Exception as e:
            logger.error(f"Script 3 failed: {e}", exc_info=True)

    thread = threading.Thread(target=background_task, args=(input_path, app.config['OUTPUT_FOLDER'], current_user.username))
    thread.start()

    flash('Script 3 is now running in the background.', 'info')
    return redirect(url_for('dashboard'))

@app.route('/script4', methods=['POST'])
@login_required
def script4():
    file = request.files.get('input_file')
    month = request.form.get('month', 'Mayo')
    year = request.form.get('year', '2024')
    target_codes_str = request.form.get('target_codes', '')  # Comma-separated
    target_codes = [code.strip() for code in target_codes_str.split(',') if code.strip()]

    if not file:
        flash('No input file provided.', 'danger')
        logger.warning("Script 4: No file uploaded by %s", current_user.username)
        return redirect(url_for('dashboard'))

    filename = secure_filename(file.filename)
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(input_path)

    def background_task(input_path, output_dir, month, year, target_codes, username):
        try:
            logger.info(f"Script 4 started by {username} for {month}-{year}, codes={target_codes}")
            process_accounts_script4(input_path, output_dir, month, year, target_codes)
            logger.info("Script 4 completed.")
        except Exception as e:
            logger.error(f"Script 4 error: {e}", exc_info=True)

    thread = threading.Thread(target=background_task, args=(input_path, app.config['OUTPUT_FOLDER'], month, year, target_codes, current_user.username))
    thread.start()

    flash('Script 4 is now running in the background.', 'info')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True)