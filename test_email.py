import smtplib
import ssl
import os
import certifi # <--- NEW IMPORT
from dotenv import load_dotenv

load_dotenv()

sender_email = os.environ.get("MAIL_USERNAME")
password = os.environ.get("MAIL_PASSWORD")
receiver_email = sender_email 

print("\n--- 📧 EMAIL DIAGNOSTIC TOOL (SSL FIXED) ---")
print(f"1. User: {sender_email}")

try:
    # THE FIX: Tell SSL exactly where to look for certificates
    context = ssl.create_default_context(cafile=certifi.where()) # <--- MAGIC FIX
    
    print("2. Connecting to Gmail...")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        print("3. Logging in...")
        server.login(sender_email, password)
        print("   ✅ Login Successful!")
        
        print("4. Sending Test Message...")
        server.sendmail(sender_email, receiver_email, "Subject: SSL Fix Works!\n\nThis is the test email.")
        print("   ✅ Email Handed to Google!")

except Exception as e:
    print(f"   ❌ ERROR: {e}")

print("--------------------------------\n")