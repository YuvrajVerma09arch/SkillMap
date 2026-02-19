import smtplib
import ssl
import os
import re
import socket
import certifi 
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

# --- CORE HELPER: SENDING LOGIC ---
def _send_smtp_email(user_email, subject, html_content):
    sender_email = os.environ.get('MAIL_USERNAME')
    sender_password = os.environ.get('MAIL_PASSWORD')
    
    if not sender_email or not sender_password:
        return False, "Email configuration missing."

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"SkillMap AI <{sender_email}>"
    message["To"] = user_email
    
    part = MIMEText(html_content, "html")
    message.attach(part)

    context = ssl.create_default_context()

    print(f"📨 STARTING EMAIL SEND PROCESS...")
    print(f"   To: {user_email}")

    try:
        # --- THE FIX: Force IPv4 Resolution ---
        # 1. Get the IPv4 address for smtp.gmail.com
        #    AF_INET means "IPv4 only"
        gmail_ip_info = socket.getaddrinfo('smtp.gmail.com', 587, family=socket.AF_INET, proto=socket.IPPROTO_TCP)
        gmail_ip_address = gmail_ip_info[0][4][0] # Extract the IP "142.250.x.x"
        
        print(f"   Resolved Gmail to IPv4: {gmail_ip_address}")
        print("   Connecting via Port 587...")

        # 2. Connect using the IP address, NOT the domain name
        with smtplib.SMTP(gmail_ip_address, 587, timeout=30) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            
            print("   Logging in...")
            server.login(sender_email, sender_password)
            
            print("   Sending email...")
            server.sendmail(sender_email, user_email, message.as_string())
            
        print("✅ EMAIL SENT SUCCESSFULLY!")
        return True, "Email sent successfully."

    except Exception as e:
        print(f"❌ FAILED TO SEND EMAIL: {str(e)}")
        # If IPv4 fails, try one last desperation fallback to standard
        try:
             print("   ⚠️ Retrying with standard connection...")
             with smtplib.SMTP('smtp.gmail.com', 587, timeout=30) as server:
                server.starttls(context=context)
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, user_email, message.as_string())
             return True, "Sent on retry."
        except:
             return False, f"Network Error: {str(e)}"

# --- 1. ROADMAP EMAIL (Keep Existing) ---
def format_roadmap_html(user_name, target_role, roadmap):
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
    subject = f"Your Career Roadmap: {target_role} 🚀"
    html_content = format_roadmap_html(user_name, target_role, roadmap_data)
    return _send_smtp_email(user_email, subject, html_content)

# --- 2. NEW: RECRUITER EMAILS ---

def send_interview_invite(candidate_email, candidate_name, job_title, recruiter_email):
    subject = f"Interview Invitation: {job_title}"
    html = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: auto; border: 1px solid #ddd; border-radius: 10px; padding: 20px;">
        <h2 style="color: #2563EB;">Good News! You've been Shortlisted.</h2>
        <p>Hi <strong>{candidate_name}</strong>,</p>
        <p>We reviewed your profile for the <strong>{job_title}</strong> position and we are impressed!</p>
        <p>We would like to invite you for an interview to discuss your skills further.</p>
        <div style="background: #f8fafc; padding: 15px; border-left: 4px solid #2563EB; margin: 20px 0;">
            <strong>Next Steps:</strong><br>
            Please reply to this email (<a href="mailto:{recruiter_email}">{recruiter_email}</a>) to schedule a time.
        </div>
        <p>Best regards,<br>The Hiring Team</p>
    </div>
    """
    return _send_smtp_email(candidate_email, subject, html)

def send_job_offer(candidate_email, candidate_name, job_title):
    subject = f"🎉 Job Offer: {job_title}"
    html = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: auto; border: 1px solid #ddd; border-radius: 10px; padding: 20px;">
        <h2 style="color: #10b981;">Congratulations! You're Hired!</h2>
        <p>Dear <strong>{candidate_name}</strong>,</p>
        <p>We are thrilled to offer you the position of <strong>{job_title}</strong>!</p>
        <p>After reviewing your interview performance, we believe you are the perfect fit for our team. You will receive a formal offer letter shortly.</p>
        <p>Welcome aboard! 🚀</p>
    </div>
    """
    return _send_smtp_email(candidate_email, subject, html)

def send_rejection(candidate_email, candidate_name, job_title):
    subject = f"Update on your application for {job_title}"
    html = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: auto; border: 1px solid #ddd; border-radius: 10px; padding: 20px;">
        <h2 style="color: #64748b;">Application Update</h2>
        <p>Dear <strong>{candidate_name}</strong>,</p>
        <p>Thank you for giving us the opportunity to consider you for the <strong>{job_title}</strong> role.</p>
        <p>While your skills are impressive, we have decided to move forward with other candidates who match our specific needs more closely at this time.</p>
        <p>We have added your resume to our talent pool for future openings.</p>
        <p>Best wishes in your job search.</p>
    </div>
    """
    return _send_smtp_email(candidate_email, subject, html)