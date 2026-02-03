import smtplib
import ssl
import os
import re
import certifi # <--- CRITICAL IMPORT
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# 1. LOAD .ENV
basedir = os.path.abspath(os.path.dirname(__file__))
root_dir = os.path.join(basedir, '..', '..')
env_path = os.path.join(root_dir, '.env')

if os.path.exists(env_path):
    load_dotenv(env_path)

def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None

def format_roadmap_html(user_name, target_role, roadmap):
    # (Simplified HTML for brevity - paste your full HTML function here if you want the pretty version)
    html = f"""
    <div style="font-family: 'Helvetica', sans-serif; color: #333; max-width: 600px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 10px; overflow: hidden;">
        <div style="background: #2563EB; padding: 30px; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 24px;">SkillMap Roadmap</h1>
            <p style="color: #bfdbfe; margin: 10px 0 0; font-size: 16px;">Target Role: <strong>{target_role}</strong></p>
        </div>
        <div style="padding: 30px; background: #fff;">
            <p style="font-size: 16px;">Hi {user_name},</p>
            <p style="color: #64748b;">Here is your personalized roadmap.</p>
            <hr style="margin: 20px 0; border: 0; border-top: 1px solid #eee;">
    """
    
    # Loop Logic
    if isinstance(roadmap, list):
        for step in roadmap:
            month = step.get('month', 'Phase')
            topic = step.get('topic', 'Topic')
            desc = step.get('description', '')
            html += f"""
            <div style="margin-bottom: 20px;">
                <span style="background: #eff6ff; color: #2563EB; padding: 4px 10px; border-radius: 15px; font-size: 12px; font-weight: bold;">{month}</span>
                <h3 style="margin: 5px 0; color: #1e3a8a;">{topic}</h3>
                <p style="color: #64748b; font-size: 14px;">{desc}</p>
            </div>
            """
    
    html += "</div></div>"
    return html

def send_roadmap_email(user_email, user_name, target_role, roadmap_data):
    print(f"\n📨 STARTING EMAIL SEND PROCESS...")
    
    if not is_valid_email(user_email):
        return False, "Invalid email format."

    SENDER_EMAIL = os.environ.get("MAIL_USERNAME")
    SENDER_PASSWORD = os.environ.get("MAIL_PASSWORD")

    if not SENDER_EMAIL or not SENDER_PASSWORD:
        return False, "Server credentials missing."

    message = MIMEMultipart("alternative")
    message["Subject"] = f"Your Career Roadmap: {target_role} 🚀"
    message["From"] = SENDER_EMAIL
    message["To"] = user_email

    html_content = format_roadmap_html(user_name, target_role, roadmap_data)
    part = MIMEText(html_content, "html")
    message.attach(part)

    try:
        # THE FIX: Use Certifi for SSL Context
        context = ssl.create_default_context(cafile=certifi.where())
        
        print("   Connecting to Google...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, user_email, message.as_string())
            print("✅ Email sent successfully!")
            
        return True, "Email sent successfully!"

    except Exception as e:
        print(f"❌ SMTP Error: {e}")
        return False, f"Failed to send: {str(e)}"