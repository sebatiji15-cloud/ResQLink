# ═══════════════════════════════════════════════════════════════
#  ResQLink — Email Configuration
#  ✏️  Set these values in your local .env file (see .env.example)
#      Do NOT put real credentials in this file — it is committed to git.
# ═══════════════════════════════════════════════════════════════
import os

# Your Gmail address (used as the sender)
EMAIL_ADDRESS  = os.environ.get('EMAIL_ADDRESS', 'your_email@gmail.com')

# Your Gmail App Password (16 characters)
# How to get it:
#   1. Go to myaccount.google.com
#   2. Security → Turn ON 2-Step Verification
#   3. Search "App Passwords" → Create → name it "ResQLink"
#   4. Copy the 16-character password into EMAIL_PASSWORD in your .env file
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', 'your_app_password_here')

# Set EMAIL_ENABLED=True in your .env file after filling the two values above
EMAIL_ENABLED  = os.environ.get('EMAIL_ENABLED', 'False').lower() == 'true'

# Do NOT change these lines
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
