import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# =========================
# ⚙️ CONFIG
# =========================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

SENDER_EMAIL = "saanvi1149@gmail.com"
SENDER_PASSWORD = "ltsh ejfo xyxt cexd"  # ⚠️ use app password only
ADMIN_EMAIL = "2024rithunya.s@vidyashilp.edu.in"

# =========================
# 📩 SEND EMAIL TO ADMIN
# =========================
def send_email_to_admin(user_email, query):
    try:
        subject = "📩 New Query from VURA Chatbot"

        body = f"""
New query received from chatbot:

----------------------------------------
User Email: {user_email}

Query:
{query}

----------------------------------------
Please respond to the user directly.
"""

        # ✅ create message
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = ADMIN_EMAIL
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        # 🔐 connect to Gmail
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)

        # 📤 send email
        server.send_message(msg)

        # ✅ close connection properly
        server.quit()

        print("✅ Email sent to admin")

        return {
            "status": "success",
            "message": "Your query has been sent to admin. You will be contacted soon."
        }

    except Exception as e:
        print("❌ Email error:", str(e))

        return {
            "status": "error",
            "message": "Failed to send email. Please try again later."
        }