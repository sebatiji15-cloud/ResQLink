═══════════════════════════════════════════════════════════════
  ResQLink – Emergency Response System
  Setup Guide
═══════════════════════════════════════════════════════════════

── REQUIREMENTS ────────────────────────────────────────────────
  • Python 3.8+
  • XAMPP (Apache + MySQL running)
  • pip install flask mysql-connector-python werkzeug

── DATABASE SETUP ──────────────────────────────────────────────
  1. Open XAMPP → Start Apache & MySQL
  2. Open phpMyAdmin → http://localhost/phpmyadmin
  3. Click SQL tab → paste contents of database_setup.sql → Go

── EMAIL SETUP (IMPORTANT) ─────────────────────────────────────
  Open app.py and find these lines (around line 21-25):

    EMAIL_ADDRESS  = 'your_email@gmail.com'
    EMAIL_PASSWORD = 'your_app_password_here'
    EMAIL_ENABLED  = False

  STEP 1: Set EMAIL_ADDRESS to your Gmail
          e.g. EMAIL_ADDRESS = 'resqlink.system@gmail.com'

  STEP 2: Get a Gmail App Password:
          → Go to myaccount.google.com
          → Security → 2-Step Verification (TURN ON if not already)
          → Search "App Passwords" at the top
          → Select app: Mail, Device: Other → type "ResQLink" → Generate
          → Copy the 16-character password shown

  STEP 3: Set EMAIL_PASSWORD to the App Password (no spaces needed)
          e.g. EMAIL_PASSWORD = 'abcdabcdabcdabcd'

  STEP 4: Set EMAIL_ENABLED = True

  Save app.py and restart the Flask server.

── HOW VOLUNTEER EMAIL WORKS ───────────────────────────────────
  1. Volunteer fills out registration form with their email
  2. After submission → "Waiting for Admin Approval" page shown
  3. Admin logs in → sees pending applications
  4. Admin clicks "Approve" → system generates unique VID-XXXXXX
  5. Email is automatically sent TO THE VOLUNTEER'S REGISTERED EMAIL
     with their unique Volunteer ID
  6. Volunteer checks their inbox → uses VID + password to login

  NOTE: Your Gmail (EMAIL_ADDRESS) is the SENDER.
        The volunteer's email (from registration) is the RECEIVER.

── RUN THE APP ─────────────────────────────────────────────────
  python app.py
  Open browser: http://localhost:5000

── DEFAULT ACCOUNTS ────────────────────────────────────────────
  Admin:     admin@resqlink.com   / Admin123
  User:      user@resqlink.com    / Test123
  Volunteer: VID-000001           / Test123  (via Volunteer Login)

═══════════════════════════════════════════════════════════════
