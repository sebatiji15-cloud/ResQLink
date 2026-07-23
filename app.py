from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import mysql.connector
from mysql.connector import Error
import hashlib
import re
import random
import string
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()  # reads variables from a local .env file (never committed to git)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')
if not app.secret_key:
    raise RuntimeError(
        "SECRET_KEY is not set. Copy .env.example to .env and fill in a random secret key."
    )

# ── Email Config ─────────────────────────────────────────────────────────────
# ✏️  Set EMAIL_ADDRESS / EMAIL_PASSWORD / EMAIL_ENABLED in your .env file
# ─────────────────────────────────────────────────────────────────────────────
from email_config import EMAIL_ADDRESS, EMAIL_PASSWORD, EMAIL_ENABLED, EMAIL_HOST, EMAIL_PORT

def send_email(to_email, subject, html_body):
    """Send HTML email via Gmail SMTP. Returns True on success."""
    if not EMAIL_ENABLED:
        print(f"[EMAIL SKIPPED] Set EMAIL_ENABLED=True and configure EMAIL_ADDRESS/PASSWORD in app.py")
        print(f"  Would send → To: {to_email} | Subject: {subject}")
        return False
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = f'ResQLink <{EMAIL_ADDRESS}>'
        msg['To']      = to_email
        msg.attach(MIMEText(html_body, 'html'))
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
        print(f"[EMAIL SENT ✓] To: {to_email} | Subject: {subject}")
        return True
    except smtplib.SMTPAuthenticationError:
        print("[EMAIL ERROR] Authentication failed — use Gmail App Password, not your normal Gmail password.")
        return False
    except smtplib.SMTPException as e:
        print(f"[EMAIL ERROR - SMTP] {e}")
        return False
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False

# ── File Upload Config ────────────────────────────────────────────────────────
UPLOAD_FOLDER      = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'}
MAX_FILE_SIZE      = 5 * 1024 * 1024  # 5MB

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER']       = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH']  = MAX_FILE_SIZE

# ── Database Config ───────────────────────────────────────────────────────────
# Reads from .env — see .env.example for defaults matching a local XAMPP install
DB = dict(
    host=os.environ.get('DB_HOST', 'localhost'),
    user=os.environ.get('DB_USER', 'root'),
    password=os.environ.get('DB_PASSWORD', ''),
    database=os.environ.get('DB_NAME', 'resqlink_db'),
)

def get_db():
    try:
        return mysql.connector.connect(**DB)
    except Error as e:
        print(f"[DB ERROR] {e}")
        return None

def hashpw(p):
    return hashlib.sha256(p.encode()).hexdigest()

# ── Volunteer ID Generator ────────────────────────────────────────────────────
def generate_volunteer_id():
    digits = ''.join(random.choices(string.digits, k=6))
    return f"VID-{digits}"

# ── File Upload Helper ────────────────────────────────────────────────────────
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_upload_file(file):
    if file and file.filename and allowed_file(file.filename):
        filename  = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
        filename  = timestamp + filename
        filepath  = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return filename
    return None

# ── Validation Helpers ────────────────────────────────────────────────────────
def validate_email(email):
    return bool(re.match(r'^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$', email))

def validate_phone(phone):
    digits = re.sub(r'\D', '', phone)
    return bool(re.match(r'^[6-9]\d{9}$', digits))

def validate_password(pw):
    if len(pw) < 6:
        return False, 'Password must be at least 6 characters.'
    if not re.search(r'[A-Za-z]', pw):
        return False, 'Password must contain at least one letter.'
    if not re.search(r'\d', pw):
        return False, 'Password must contain at least one number.'
    return True, ''

def validate_name(name):
    return bool(re.match(r'^[A-Za-z\s]{2,}$', name))

# ── Email Templates ───────────────────────────────────────────────────────────
def approval_email_html(vol_name, vid, vol_email, plain_password):
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;border:1px solid #e0e0e0;border-radius:12px;overflow:hidden;">
      <div style="background:linear-gradient(135deg,#1976d2,#1565c0);padding:36px 24px;text-align:center;">
        <h1 style="color:#fff;margin:0;font-size:2rem;">🎉 Congratulations!</h1>
        <p style="color:#bbdefb;margin:10px 0 0;font-size:1rem;">Your ResQLink volunteer application has been approved</p>
      </div>
      <div style="padding:36px 28px;">
        <p style="font-size:1rem;color:#333;">Dear <strong>{vol_name}</strong>,</p>
        <p style="color:#555;line-height:1.8;">
          We are pleased to inform you that your volunteer application on <strong>ResQLink</strong>
          has been <span style="color:#2e7d32;font-weight:bold;">approved</span> by our admin team.
          Below are your login credentials to access the Volunteer Portal.
        </p>

        <!-- Credentials Box -->
        <div style="background:#f1f8e9;border:2px solid #66bb6a;border-radius:10px;padding:24px 28px;margin:28px 0;">
          <h3 style="margin:0 0 16px;color:#2e7d32;font-size:1rem;text-transform:uppercase;letter-spacing:1px;">
            🔐 Your Login Credentials
          </h3>
          <table style="width:100%;border-collapse:collapse;">
            <tr>
              <td style="padding:10px 12px;background:#fff;border-radius:6px 6px 0 0;border-bottom:1px solid #e0e0e0;">
                <span style="color:#777;font-size:0.85rem;">Volunteer ID</span><br>
                <strong style="font-size:1.5rem;color:#1b5e20;letter-spacing:3px;">{vid}</strong>
              </td>
            </tr>
            <tr>
              <td style="padding:10px 12px;background:#fff;border-bottom:1px solid #e0e0e0;">
                <span style="color:#777;font-size:0.85rem;">Email Address</span><br>
                <strong style="font-size:1.1rem;color:#1b5e20;">{vol_email}</strong>
              </td>
            </tr>
            <tr>
              <td style="padding:10px 12px;background:#fff;border-radius:0 0 6px 6px;">
                <span style="color:#777;font-size:0.85rem;">Password</span><br>
                <strong style="font-size:1.2rem;color:#1b5e20;letter-spacing:2px;">{plain_password}</strong>
              </td>
            </tr>
          </table>
        </div>

        <!-- How to Login -->
        <div style="background:#e3f2fd;border-radius:10px;padding:18px 22px;margin:0 0 24px;">
          <p style="margin:0 0 8px;color:#1565c0;font-weight:700;">📋 How to Login:</p>
          <ol style="margin:0;padding-left:20px;color:#37474f;line-height:1.9;">
            <li>Go to <strong>ResQLink → Volunteer Login</strong></li>
            <li>Enter your <strong>Volunteer ID: {vid}</strong> OR <strong>Email: {vol_email}</strong></li>
            <li>Enter your <strong>Password</strong> as shown above</li>
            <li>Click <strong>Login</strong> to access your dashboard</li>
          </ol>
        </div>

        <!-- Warning -->
        <div style="background:#fff8e1;border-left:4px solid #ffb300;border-radius:6px;padding:14px 18px;margin:0 0 24px;">
          <p style="margin:0;color:#e65100;font-size:0.9rem;">
            ⚠️ <strong>Important:</strong> Keep your Volunteer ID, Email, and password safe.
            Do not share them with anyone. You can change your password after logging in.
          </p>
        </div>

        <p style="color:#555;line-height:1.8;">
          Thank you for joining our mission to save lives. We look forward to working with you!
        </p>
        <p style="color:#333;margin-top:24px;">
          Warm regards,<br>
          <strong>ResQLink Admin Team</strong>
        </p>
      </div>
      <div style="background:#f5f5f5;padding:16px 24px;text-align:center;border-top:1px solid #e0e0e0;">
        <p style="margin:0;color:#666;font-size:0.85rem;">
          ResQLink Emergency Response Network | Connecting volunteers with those in need
        </p>
      </div>
    </div>
    """

def rejection_email_html(vol_name, admin_notes=''):
    notes_html = f'<p style="color:#d32f2f;background:#ffebee;padding:12px;border-radius:6px;margin:16px 0;"><strong>Admin Notes:</strong><br>{admin_notes}</p>' if admin_notes else ''
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;border:1px solid #e0e0e0;border-radius:12px;overflow:hidden;">
      <div style="background:linear-gradient(135deg,#d32f2f,#c62828);padding:36px 24px;text-align:center;">
        <h1 style="color:#fff;margin:0;font-size:2rem;">Application Status Update</h1>
        <p style="color:#ffcdd2;margin:10px 0 0;font-size:1rem;">Your ResQLink volunteer application</p>
      </div>
      <div style="padding:36px 28px;">
        <p style="font-size:1rem;color:#333;">Dear <strong>{vol_name}</strong>,</p>
        <p style="color:#555;line-height:1.8;">
          Thank you for applying to become a ResQLink volunteer. After careful review, we regret to inform you that your application has been <span style="color:#d32f2f;font-weight:bold;">not approved</span> at this time.
        </p>
        {notes_html}
        <p style="color:#555;line-height:1.8;">
          You are welcome to reapply after addressing any concerns. If you have questions, please contact our admin team.
        </p>
        <p style="color:#333;margin-top:24px;">
          Best regards,<br>
          <strong>ResQLink Admin Team</strong>
        </p>
      </div>
      <div style="background:#f5f5f5;padding:16px 24px;text-align:center;border-top:1px solid #e0e0e0;">
        <p style="margin:0;color:#666;font-size:0.85rem;">
          ResQLink Emergency Response Network
        </p>
      </div>
    </div>
    """

# ─────────────────────────────────────────────────────────────────────────────
# HOME PAGE
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

# ─────────────────────────────────────────────────────────────────────────────
# USER REGISTER
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name    = request.form.get('name', '').strip()
        email   = request.form.get('email', '').strip().lower()
        phone   = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        pw_raw  = request.form.get('password', '')
        pw_conf = request.form.get('password_confirm', '')

        errors = []
        if not name or not validate_name(name):
            errors.append('Name must be at least 2 letters.')
        if not email or not validate_email(email):
            errors.append('Invalid email address.')
        if not phone or not validate_phone(phone):
            errors.append('Phone must be a valid 10-digit Indian number.')
        if not address or len(address) < 3:
            errors.append('Address must be at least 3 characters.')
        if pw_conf and pw_raw != pw_conf:
            errors.append('Passwords do not match.')
        pw_ok, pw_msg = validate_password(pw_raw)
        if not pw_ok:
            errors.append(pw_msg)

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('register.html')

        db = get_db()
        if not db:
            flash('Database error. Is XAMPP MySQL running?', 'error')
            return render_template('register.html')

        cur = db.cursor()
        try:
            cur.execute("SELECT id FROM users WHERE email=%s", (email,))
            if cur.fetchone():
                flash('This email is already registered.', 'error')
                cur.close(); db.close()
                return render_template('register.html')

            cur.execute(
                "INSERT INTO users (name, email, phone, address, password) VALUES(%s,%s,%s,%s,%s)",
                (name, email, phone, address, hashpw(pw_raw))
            )
            db.commit()
            flash('✅ Registration successful! Please login.', 'success')
            cur.close(); db.close()
            return redirect(url_for('login'))
        except Error as e:
            flash(f'Registration error: {str(e)}', 'error')
            cur.close(); db.close()
            return render_template('register.html')

    return render_template('register.html')

# ─────────────────────────────────────────────────────────────────────────────
# USER LOGIN
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        pw    = request.form.get('password', '')

        errors = []
        if not email:
            errors.append('Email is required.')
        if len(pw) < 1:
            errors.append('Password is required.')
        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('login.html')

        db = get_db()
        if not db:
            flash('Database error. Is XAMPP MySQL running?', 'error')
            return render_template('login.html')

        cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, hashpw(pw)))
        user = cur.fetchone()
        cur.close(); db.close()

        if user:
            session['uid']   = user['id']
            session['uname'] = user['name']
            session['urole'] = 'user'
            flash(f"Welcome, {user['name']}!", 'success')
            return redirect(url_for('user_dashboard'))
        flash('Invalid email or password.', 'error')

    return render_template('login.html')

# ─────────────────────────────────────────────────────────────────────────────
# ADMIN LOGIN
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        pw    = request.form.get('password', '')

        errors = []
        if not email:
            errors.append('Email is required.')
        if len(pw) < 1:
            errors.append('Password is required.')
        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('admin_login.html')

        db = get_db()
        if not db:
            flash('Database error. Is XAMPP MySQL running?', 'error')
            return render_template('admin_login.html')

        cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE email=%s AND password=%s AND email='admin@resqlink.com'", (email, hashpw(pw)))
        admin = cur.fetchone()
        cur.close(); db.close()

        if admin:
            session['uid']   = admin['id']
            session['uname'] = admin['name']
            session['urole'] = 'admin'
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin'))
        flash('Invalid admin credentials.', 'error')

    return render_template('admin_login.html')

# ─────────────────────────────────────────────────────────────────────────────
# VOLUNTEER APPLY
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/volunteer/apply', methods=['GET', 'POST'])
def vol_apply():
    if request.method == 'POST':
        name    = request.form.get('name', '').strip()
        email   = request.form.get('email', '').strip().lower()
        phone   = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        pw_raw  = request.form.get('password', '')
        pw_conf = request.form.get('password_confirm', '')
        cert_file   = request.files.get('certificate')
        degree_file = request.files.get('degree')

        errors = []
        if not name or not validate_name(name):
            errors.append('Name must be at least 2 letters.')
        if not email or not validate_email(email):
            errors.append('Invalid email address.')
        if not phone or not validate_phone(phone):
            errors.append('Phone must be a valid 10-digit Indian number.')
        if not address or len(address) < 3:
            errors.append('Address must be at least 3 characters.')
        if pw_raw != pw_conf:
            errors.append('Passwords do not match.')
        pw_ok, pw_msg = validate_password(pw_raw)
        if not pw_ok:
            errors.append(pw_msg)
        if not cert_file or not allowed_file(cert_file.filename):
            errors.append('Certificate file is required (PDF, JPG, PNG, DOC, DOCX).')
        if not degree_file or not allowed_file(degree_file.filename):
            errors.append('Degree file is required (PDF, JPG, PNG, DOC, DOCX).')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('vol_apply.html')

        db = get_db()
        if not db:
            flash('Database error. Is XAMPP MySQL running?', 'error')
            return render_template('vol_apply.html')

        cur = db.cursor()
        # ✅ CHECK: Email must be unique across both users and volunteer_applications and volunteers
        cur.execute("SELECT id FROM volunteer_applications WHERE email=%s", (email,))
        if cur.fetchone():
            flash('This email already has a pending application. Please wait for admin approval.', 'error')
            cur.close(); db.close()
            return render_template('vol_apply.html')
        
        cur.execute("SELECT id FROM volunteers WHERE email=%s", (email,))
        if cur.fetchone():
            flash('This email is already registered as a volunteer. Please use a different email.', 'error')
            cur.close(); db.close()
            return render_template('vol_apply.html')
        
        cur.execute("SELECT id FROM users WHERE email=%s", (email,))
        if cur.fetchone():
            flash('This email is already registered as a user. Please use a different email.', 'error')
            cur.close(); db.close()
            return render_template('vol_apply.html')

        cert_filename   = save_upload_file(cert_file)
        degree_filename = save_upload_file(degree_file)

        if not cert_filename or not degree_filename:
            flash('Error uploading files. Please try again.', 'error')
            cur.close(); db.close()
            return render_template('vol_apply.html')

        # Store BOTH hashed password (for login) and plain password (to email on approval)
        cur.execute(
            """INSERT INTO volunteer_applications
               (name, email, phone, address, password, plain_password, certificate_file, degree_file, status)
               VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'pending')""",
            (name, email, phone, address, hashpw(pw_raw), pw_raw, cert_filename, degree_filename)
        )
        db.commit()
        cur.close(); db.close()
        return redirect(url_for('pending_approval'))

    return render_template('vol_apply.html')

# ─────────────────────────────────────────────────────────────────────────────
# PENDING APPROVAL PAGE
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/volunteer/pending-approval')
def pending_approval():
    return render_template('pending_approval.html')

# ─────────────────────────────────────────────────────────────────────────────
# VOLUNTEER LOGIN (with Volunteer ID OR Email) ✅ ENHANCED
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/volunteer/login', methods=['GET', 'POST'])
def vol_login():
    if request.method == 'POST':
        login_input = request.form.get('login_input', '').strip()  # Can be VID or Email
        pw          = request.form.get('password', '')

        errors = []
        if not login_input:
            errors.append('Volunteer ID or Email is required.')
        if len(pw) < 1:
            errors.append('Password is required.')
        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('vol_login.html')

        db = get_db()
        if not db:
            flash('Database error. Is XAMPP MySQL running?', 'error')
            return render_template('vol_login.html')

        cur = db.cursor(dictionary=True)
        
        # ✅ ENHANCED: Try to match by Volunteer ID OR Email
        volunteer = None
        login_input_upper = login_input.upper()
        
        # First try Volunteer ID match
        if login_input_upper.startswith('VID-'):
            cur.execute("SELECT * FROM volunteers WHERE volunteer_id=%s AND password=%s", 
                       (login_input_upper, hashpw(pw)))
            volunteer = cur.fetchone()
        
        # If not found, try Email match
        if not volunteer:
            cur.execute("SELECT * FROM volunteers WHERE email=%s AND password=%s", 
                       (login_input.lower(), hashpw(pw)))
            volunteer = cur.fetchone()
        
        cur.close(); db.close()

        if volunteer:
            session['uid']          = volunteer['id']
            session['uname']        = volunteer['name']
            session['urole']        = 'volunteer'
            session['volunteer_id'] = volunteer['volunteer_id']
            session['email']        = volunteer['email']
            flash(f"Welcome back, {volunteer['name']}!", 'success')
            return redirect(url_for('vol_dashboard'))
        
        flash('Invalid Volunteer ID/Email or password.', 'error')

    return render_template('vol_login.html')

# ─────────────────────────────────────────────────────────────────────────────
# USER DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/user/dashboard')
def user_dashboard():
    if 'uid' not in session or session.get('urole') != 'user':
        flash('Please login as a user to access this page.', 'error')
        return redirect(url_for('login'))

    db  = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT r.*, v.name vol_name, v.phone vol_phone, v.email vol_email
        FROM requests r
        LEFT JOIN volunteers v ON r.volunteer_id = v.id
        WHERE r.user_id=%s
        ORDER BY r.created_at DESC
    """, (session['uid'],))
    my_reqs = cur.fetchall()
    cur.close(); db.close()
    return render_template('user_dashboard.html', requests=my_reqs)

# ─────────────────────────────────────────────────────────────────────────────
# CREATE EMERGENCY REQUEST
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/user/create-request', methods=['GET', 'POST'])
def create_request():
    if 'uid' not in session or session.get('urole') != 'user':
        flash('Please login as a user to access this page.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        etype       = request.form.get('type', '').strip()
        description = request.form.get('description', '').strip()
        location    = request.form.get('location', '').strip()
        latitude    = request.form.get('latitude', '').strip()
        longitude   = request.form.get('longitude', '').strip()

        errors = []
        if not etype or len(etype) < 3:
            errors.append('Emergency type must be at least 3 characters.')
        if not description or len(description) < 10:
            errors.append('Description must be at least 10 characters.')
        if not location or len(location) < 3:
            errors.append('Location must be at least 3 characters.')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('create_request.html')

        db = get_db()
        cur = db.cursor()
        cur.execute("""
            INSERT INTO requests (user_id, etype, description, location, latitude, longitude, status)
            VALUES(%s, %s, %s, %s, %s, %s, 'pending')
        """, (session['uid'], etype, description, location, latitude, longitude))
        db.commit()
        cur.close(); db.close()

        flash('✅ Emergency request created! Volunteers will respond soon.', 'success')
        return redirect(url_for('user_dashboard'))

    return render_template('create_request.html')

# ─────────────────────────────────────────────────────────────────────────────
# VOLUNTEER DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/volunteer/dashboard')
def vol_dashboard():
    if 'uid' not in session or session.get('urole') != 'volunteer':
        flash('Please login as a volunteer to access this page.', 'error')
        return redirect(url_for('vol_login'))

    db  = get_db()
    cur = db.cursor(dictionary=True)
    
    # Get volunteer info
    cur.execute("SELECT * FROM volunteers WHERE id=%s", (session['uid'],))
    vol_info = cur.fetchone()
    
    # Get active requests (pending or already assigned to this volunteer)
    cur.execute("""
        SELECT r.*, u.name req_name, u.email req_email, u.phone req_phone
        FROM requests r
        JOIN users u ON r.user_id = u.id
        WHERE r.status IN ('pending', 'active') AND (r.volunteer_id IS NULL OR r.volunteer_id=%s)
        ORDER BY r.created_at DESC LIMIT 10
    """, (session['uid'],))
    available_reqs = cur.fetchall()
    
    # Get my assigned requests
    cur.execute("""
        SELECT r.*, u.name req_name, u.email req_email, u.phone req_phone
        FROM requests r
        JOIN users u ON r.user_id = u.id
        WHERE r.volunteer_id=%s
        ORDER BY r.created_at DESC
    """, (session['uid'],))
    my_reqs = cur.fetchall()
    
    cur.close(); db.close()
    return render_template('vol_dashboard.html', vol_info=vol_info, 
                          available_reqs=available_reqs, my_reqs=my_reqs)

# ─────────────────────────────────────────────────────────────────────────────
# ACCEPT REQUEST (Volunteer accepts a request)
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/volunteer/accept-request/<int:req_id>', methods=['POST'])
def accept_request(req_id):
    if 'uid' not in session or session.get('urole') != 'volunteer':
        return redirect(url_for('vol_login'))

    db = get_db()
    cur = db.cursor()
    cur.execute("""
        UPDATE requests
        SET volunteer_id=%s, status='active', responded_at=NOW()
        WHERE id=%s
    """, (session['uid'], req_id))
    db.commit()
    cur.close(); db.close()

    flash('✅ Request accepted! You are now assigned to this emergency.', 'success')
    return redirect(url_for('vol_dashboard'))

# ─────────────────────────────────────────────────────────────────────────────
# RESOLVE REQUEST (Volunteer marks request as resolved)
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/volunteer/resolve-request/<int:req_id>', methods=['POST'])
def resolve_request(req_id):
    if 'uid' not in session or session.get('urole') != 'volunteer':
        return redirect(url_for('vol_login'))

    db = get_db()
    cur = db.cursor()
    cur.execute("""
        UPDATE requests
        SET status='resolved', resolved_at=NOW()
        WHERE id=%s AND volunteer_id=%s
    """, (req_id, session['uid']))
    db.commit()
    cur.close(); db.close()

    flash('✅ Request marked as resolved!', 'success')
    return redirect(url_for('vol_dashboard'))

# ─────────────────────────────────────────────────────────────────────────────
# ADMIN DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/admin')
def admin():
    if 'uid' not in session or session.get('urole') != 'admin':
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('login'))

    db  = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT r.*,
               u.name req_name, u.phone req_phone, u.email req_email,
               v.name vol_name, v.phone vol_phone, v.volunteer_id vol_vid, v.email vol_email
        FROM   requests r
        JOIN   users u ON r.user_id = u.id
        LEFT JOIN volunteers v ON r.volunteer_id = v.id
        ORDER  BY r.created_at DESC
    """)
    all_reqs = cur.fetchall()

    cur.execute("""
        SELECT * FROM volunteer_applications
        WHERE status='pending'
        ORDER BY applied_at DESC
    """)
    pending_apps = cur.fetchall()

    cur.execute("SELECT * FROM volunteers ORDER BY created_at DESC")
    approved_vols = cur.fetchall()

    cur.execute("SELECT * FROM users WHERE email != 'admin@resqlink.com' ORDER BY created_at DESC")
    all_users = cur.fetchall()

    cur.execute("SELECT COUNT(*) total FROM users WHERE email != 'admin@resqlink.com'")
    total_users = cur.fetchone()['total']
    cur.execute("SELECT COUNT(*) total FROM volunteers")
    total_vols = cur.fetchone()['total']
    cur.execute("SELECT COUNT(*) total FROM requests WHERE status='pending'")
    pending = cur.fetchone()['total']
    cur.execute("SELECT COUNT(*) total FROM requests WHERE status='active'")
    active = cur.fetchone()['total']
    cur.execute("SELECT COUNT(*) total FROM requests WHERE status='resolved'")
    resolved = cur.fetchone()['total']
    cur.execute("SELECT COUNT(*) total FROM volunteer_applications WHERE status='pending'")
    pending_vol_apps = cur.fetchone()['total']

    cur.close(); db.close()
    return render_template('admin.html',
                           all_reqs=all_reqs,
                           pending_apps=pending_apps,
                           approved_vols=approved_vols,
                           all_users=all_users,
                           total_users=total_users,
                           total_vols=total_vols,
                           pending=pending,
                           active=active,
                           resolved=resolved,
                           pending_vol_apps=pending_vol_apps)

# ─────────────────────────────────────────────────────────────────────────────
# APPROVE VOLUNTEER APPLICATION ✅ ENHANCED
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/admin/approve-volunteer/<int:app_id>', methods=['POST'])
def approve_volunteer(app_id):
    if 'uid' not in session or session.get('urole') != 'admin':
        return redirect(url_for('login'))

    db  = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT * FROM volunteer_applications WHERE id=%s", (app_id,))
    vol_app = cur.fetchone()

    if not vol_app:
        flash('Application not found.', 'error')
        cur.close(); db.close()
        return redirect(url_for('admin'))

    # Generate unique Volunteer ID
    while True:
        vid = generate_volunteer_id()
        cur.execute("SELECT id FROM volunteers WHERE volunteer_id=%s", (vid,))
        if not cur.fetchone():
            break

    # Insert into volunteers table
    cur.execute("""
        INSERT INTO volunteers
        (volunteer_id, name, email, phone, address, password, certificate_file, degree_file, verified_by_admin, created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
    """, (vid, vol_app['name'], vol_app['email'], vol_app['phone'], vol_app['address'],
          vol_app['password'], vol_app['certificate_file'], vol_app['degree_file'], session.get('uname')))

    # Update application status
    cur.execute("""
        UPDATE volunteer_applications
        SET status='approved', volunteer_id=%s, verified_at=NOW()
        WHERE id=%s
    """, (vid, app_id))

    db.commit()
    cur.close(); db.close()

    # ── Send approval email with Volunteer ID, Email AND Password ────────────────
    vol_name       = vol_app['name']
    vol_email      = vol_app['email']
    plain_password = vol_app.get('plain_password', '(use the password you set during registration)')

    html = approval_email_html(vol_name, vid, vol_email, plain_password)
    email_sent = send_email(vol_email, f'ResQLink – Volunteer Approved! Your ID: {vid}', html)

    if email_sent:
        flash(f"✅ Volunteer approved! ID: {vid} | Email: {vol_email} — Email with credentials sent.", 'success')
    else:
        flash(f"✅ Volunteer approved! ID: {vid} | Email: {vol_email} — Email not sent (configure EMAIL settings in app.py).", 'success')

    return redirect(url_for('admin'))

# ─────────────────────────────────────────────────────────────────────────────
# REJECT VOLUNTEER APPLICATION
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/admin/reject-volunteer/<int:app_id>', methods=['POST'])
def reject_volunteer(app_id):
    if 'uid' not in session or session.get('urole') != 'admin':
        return redirect(url_for('login'))

    admin_notes = request.form.get('admin_notes', '').strip()

    db  = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT * FROM volunteer_applications WHERE id=%s", (app_id,))
    vol_app = cur.fetchone()

    cur.execute("""
        UPDATE volunteer_applications
        SET status='rejected', admin_notes=%s
        WHERE id=%s
    """, (admin_notes, app_id))
    db.commit()
    cur.close(); db.close()

    # ── Send rejection email ──────────────────────────────────────────────────
    if vol_app:
        html = rejection_email_html(vol_app['name'], admin_notes)
        send_email(vol_app['email'], 'ResQLink – Volunteer Application Update', html)

    flash('Volunteer application rejected.', 'success')
    return redirect(url_for('admin'))

# ─────────────────────────────────────────────────────────────────────────────
# DELETE VOLUNTEER
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/admin/delete-volunteer/<int:vol_id>', methods=['POST'])
def delete_volunteer(vol_id):
    if 'uid' not in session or session.get('urole') != 'admin':
        return redirect(url_for('login'))

    db  = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM volunteers WHERE id=%s", (vol_id,))
    db.commit()
    cur.close(); db.close()
    flash('Volunteer deleted successfully.', 'success')
    return redirect(url_for('admin'))

# ─────────────────────────────────────────────────────────────────────────────
# DELETE USER
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'uid' not in session or session.get('urole') != 'admin':
        return redirect(url_for('login'))

    db  = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
    db.commit()
    cur.close(); db.close()
    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin'))

# ─────────────────────────────────────────────────────────────────────────────
# LOGOUT
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
