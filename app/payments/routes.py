from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models import User, Transaction
from app.utils.payments import create_order, verify_payment_signature
import os

payments = Blueprint('payments', __name__)


# 1. PRICING INFO (plan metadata for the SPA)
@payments.route('/api/payments/plans', methods=['GET'])
@login_required
def plans():
    return jsonify({
        'credits': current_user.credits,
        'tier': current_user.tier,
        'plans': [
            {'id': 'starter', 'price': 0, 'credits': 3, 'name': 'Starter'},
            {'id': 'pro', 'price': 299, 'credits': 50, 'name': 'Pro'},
            {'id': 'enterprise', 'price': 499, 'credits': 200, 'name': 'Max'},
        ],
    })


# 2. CREATE ORDER (SPA calls this when user clicks "Buy")
@payments.route('/api/payments/create', methods=['POST'])
@login_required
def create_payment():
    try:
        data = request.get_json(silent=True) or {}
        plan_type = data.get('plan')

        # Bug fix: unknown/missing plans no longer silently buy "pro".
        if plan_type not in ('pro', 'enterprise'):
            return jsonify({'error': 'Invalid plan selected.'}), 400

        amount = 299  # Pro
        credits = 50

        if plan_type == 'enterprise':
            amount = 499
            credits = 200

        order_data, error = create_order(amount)
        if error:
            return jsonify({'error': error}), 500

        new_txn = Transaction(
            user_id=current_user.id,
            amount=amount,
            status='pending',
            razorpay_order_id=order_data['id'],
            credits_purchased=credits,
        )
        db.session.add(new_txn)
        db.session.commit()

        return jsonify({
            'order_id': order_data['id'],
            'amount': order_data['amount'],
            'key_id': os.environ.get('RAZORPAY_KEY_ID'),
            'user_email': current_user.email,
            'user_name': current_user.name,
        })

    except Exception:
        current_app.logger.exception('payment order creation failed')
        return jsonify({'error': 'Could not create payment order. Please try again.'}), 500


# 3. VERIFY PAYMENT (Called after Razorpay checkout succeeds)
@payments.route('/api/payments/verify', methods=['POST'])
@login_required
def verify_payment():
    data = request.get_json(silent=True) or {}

    razorpay_order_id = data.get('razorpay_order_id')
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_signature = data.get('razorpay_signature')

    if not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
        return jsonify({'status': 'failed', 'message': 'Missing payment parameters'}), 400

    is_valid = verify_payment_signature(
        razorpay_order_id, razorpay_payment_id, razorpay_signature
    )

    txn = Transaction.query.filter_by(razorpay_order_id=razorpay_order_id).first()
    if not txn:
        return jsonify({'status': 'failed', 'message': 'Transaction not found'}), 404

    # Bug fix: idempotency — a replayed verify must not credit twice.
    if txn.status == 'success':
        return jsonify({
            'status': 'success',
            'already_verified': True,
            'new_credits': current_user.credits,
        })

    if txn.user_id != current_user.id:
        return jsonify({'status': 'failed', 'message': 'Transaction belongs to another user'}), 403

    if is_valid:
        txn.status = 'success'
        txn.razorpay_payment_id = razorpay_payment_id

        current_user.credits += txn.credits_purchased
        if txn.amount >= 499:
            current_user.tier = 'Enterprise'
        else:
            current_user.tier = 'Pro'

        db.session.commit()
        return jsonify({'status': 'success', 'new_credits': current_user.credits})
    else:
        txn.status = 'failed'
        db.session.commit()
        return jsonify({'status': 'failed', 'message': 'Invalid Signature'}), 400
