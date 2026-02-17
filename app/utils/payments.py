import razorpay
import os
import hmac
import hashlib

# Initialize Razorpay Client
# MAKE SURE 'RAZORPAY_KEY_ID' and 'RAZORPAY_KEY_SECRET' are in your .env file
def get_razorpay_client():
    key_id = os.environ.get('RAZORPAY_KEY_ID')
    key_secret = os.environ.get('RAZORPAY_KEY_SECRET')
    
    if not key_id or not key_secret:
        return None
    return razorpay.Client(auth=(key_id, key_secret))

def create_order(amount_in_rupees, currency='INR'):
    """
    Creates an order ID on Razorpay.
    amount_in_rupees: The cost (e.g., 499)
    """
    client = get_razorpay_client()
    if not client:
        return None, "Razorpay credentials missing."
    
    try:
        # Razorpay expects amount in PAISE (1 Rupee = 100 Paise)
        data = {
            "amount": amount_in_rupees * 100,
            "currency": currency,
            "payment_capture": 1 # Auto-capture payment
        }
        order = client.order.create(data=data)
        return order, None
    except Exception as e:
        return None, str(e)

def verify_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
    """
    Verifies that the payment actually came from Razorpay and wasn't spoofed.
    """
    client = get_razorpay_client()
    if not client: return False

    try:
        # Razorpay provides a utility to verify parameters
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        client.utility.verify_payment_signature(params_dict)
        return True
    except razorpay.errors.SignatureVerificationError:
        return False
    except Exception as e:
        print(f"Verification Error: {e}")
        return False