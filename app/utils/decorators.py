from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user
from app import db

def check_quota(cost=1):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 1. Enterprise / Pro users might have unlimited access
            if current_user.tier == 'Enterprise':
                return f(*args, **kwargs)
            
            # 2. Check Credits
            if current_user.credits < cost:
                flash(f"You need {cost} credit(s) to use this feature. Please upgrade!", "warning")
                # Redirect to the pricing page (we will build this next)
                return redirect(url_for('payments.pricing'))
            
            # 3. Deduct Credits
            # Note: We deduct credits AFTER the feature runs successfully? 
            # Or BEFORE? Usually BEFORE is safer to prevent exploits.
            current_user.credits -= cost
            db.session.commit()
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator