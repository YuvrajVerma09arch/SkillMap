from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import User, Transaction
from app.utils.payments import create_order, verify_payment_signature
import os

payments = Blueprint('payments', __name__)

# 1. PRICING PAGE
@payments.route('/pricing')
def pricing():
    return render_template('payments/pricing.html')

# 2. CREATE ORDER (AJAX calls this when user clicks "Buy")
@payments.route('/create-payment', methods=['POST'])
@login_required
def create_payment():
    try:
        data = request.get_json()
        plan_type = data.get('plan') # 'pro' or 'enterprise'

        # DEFINE PRICING LOGIC HERE
        amount = 499 # Default Pro Price
        credits = 50 # Credits given for Pro
        
        if plan_type == 'enterprise':
            amount = 999
            credits = 200
        
        # 1. Create Razorpay Order
        order_data, error = create_order(amount)
        if error:
            return jsonify({'error': error}), 500
            
        # 2. Log Pending Transaction in DB
        new_txn = Transaction(
            user_id=current_user.id,
            amount=amount,
            status='pending',
            razorpay_order_id=order_data['id'],
            credits_purchased=credits
        )
        db.session.add(new_txn)
        db.session.commit()

        # 3. Return Order ID to Frontend
        return jsonify({
            'order_id': order_data['id'],
            'amount': order_data['amount'],
            'key_id': os.environ.get('RAZORPAY_KEY_ID'),
            'user_email': current_user.email,
            'user_name': current_user.name
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 3. VERIFY PAYMENT (Called after success)
@payments.route('/verify-payment', methods=['POST'])
@login_required
def verify_payment():
    data = request.get_json()
    
    razorpay_order_id = data.get('razorpay_order_id')
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_signature = data.get('razorpay_signature')

    # 1. Verify Signature
    is_valid = verify_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature)
    
    txn = Transaction.query.filter_by(razorpay_order_id=razorpay_order_id).first()
    if not txn:
        return jsonify({'status': 'failed', 'message': 'Transaction not found'}), 404

    if is_valid:
        # 2. Success! Update Transaction
        txn.status = 'success'
        txn.razorpay_payment_id = razorpay_payment_id
        
        # 3. Add Credits to User
        current_user.credits += txn.credits_purchased
        if txn.amount >= 999: # Example logic for Tier upgrade
            current_user.tier = 'Enterprise'
        else:
            current_user.tier = 'Pro'
            
        db.session.commit()
        return jsonify({'status': 'success', 'new_credits': current_user.credits})
    else:
        # 3. Failed
        txn.status = 'failed'
        db.session.commit()
        return jsonify({'status': 'failed', 'message': 'Invalid Signature'}), 400