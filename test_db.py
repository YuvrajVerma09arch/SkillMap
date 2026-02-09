import os
from app import create_app, db
from app.models import User
from sqlalchemy import text

def test_connection():
    # Load the Flask App
    app = create_app()
    
    with app.app_context():
        print("\n--- 🔌 DATABASE CONNECTION TEST ---")
        
        # 1. Check if URL exists
        db_url = app.config.get('SQLALCHEMY_DATABASE_URI')
        if not db_url:
            print("❌ ERROR: DATABASE_URL not found in .env config.")
            return

        # Security: Print only the host, not the password
        try:
            host = db_url.split('@')[1].split('/')[0]
            print(f"Target Host: {host}")
        except:
            print(f"Target URL: [Hidden/Complex]")

        try:
            # 2. Test Raw SQL Connection
            print("Attempting raw connection...")
            db.session.execute(text('SELECT 1'))
            print("   ✅ Raw Connection: SUCCESS")

            # 3. Test ORM (User Table)
            print("Attempting User table query...")
            user_count = User.query.count()
            print(f"   ✅ User Table Access: SUCCESS")
            print(f"   📊 Total Users in DB: {user_count}")
            
        except Exception as e:
            print(f"\n❌ CONNECTION FAILED")
            print(f"Error Details: {str(e)}")
            print("-" * 30)
            print("Troubleshooting Tips:")
            print("1. Did you install the driver? (pip install psycopg2-binary)")
            print("2. Is the Neon URL correct in .env?")
            print("3. Did you run the SQL creation script in Neon?")

        print("-" * 30 + "\n")

if __name__ == "__main__":
    test_connection()