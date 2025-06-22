# routes.py
import uuid
import requests
import os
import jwt
from flask import Blueprint, request, jsonify, current_app
from vivpayz.models import db, Transaction
from flask_jwt_extended import jwt_required, get_jwt_identity
from vivpayz.models import User, Wallet  # import your user/wallet models


paystack = Blueprint('paystack', __name__)

PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY')

def get_current_user():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"])
        user_id = payload.get("user_id")
        return User.query.get(user_id)
    except Exception as e:
        print("JWT error:", str(e))
        return None

@paystack.route('/api/paystack/initiate', methods=['POST'])
def initiate_payment():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    print("Received payload:", data)

    amount = data.get('amount')
    email = data.get('email')
    callback_url = data.get('callback_url')
    currency = 'NGN'

    if not amount or not email:
        return jsonify({'error': 'Amount and email are required'}), 400

    wallet = Wallet.query.filter_by(user_id=user.id).first()
    if not wallet:
        return jsonify({'error': 'Wallet not found'}), 404

    reference = str(uuid.uuid4())

    # Save transaction
    transaction = Transaction(
        user_id=user.id,
        wallet_id=wallet.id,
        type='credit',
        purpose='Wallet Funding',
        amount=amount,
        currency=currency,
        reference=reference,
        status='pending'
    )
    db.session.add(transaction)
    db.session.commit()

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "email": email,
        "amount": int(float(amount) * 100),
        "reference": reference,
        "currency": currency
    }
    if callback_url:
        payload["callback_url"] = callback_url

    try:
        res = requests.post("https://api.paystack.co/transaction/initialize", json=payload, headers=headers)
        paystack_res = res.json()

        if paystack_res.get("status") is True:
            return jsonify({
                "status": "success",
                "data": paystack_res["data"]
            })
        else:
            transaction.status = 'failed'
            db.session.commit()
            return jsonify({"error": "Paystack init failed", "details": paystack_res}), 400

    except Exception as e:
        transaction.status = 'failed'
        db.session.commit()
        return jsonify({'error': 'Server error', 'message': str(e)}), 500


@paystack.route('/api/paystack/verify', methods=['POST'])
def verify_payment():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    reference = data.get('reference') if data else None

    if not reference:
        return jsonify({'error': 'Reference is required'}), 400

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    try:
        res = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers)
        paystack_res = res.json()

        if not paystack_res.get("status"):
            return jsonify({'error': 'Verification failed', 'details': paystack_res}), 400

        payment_data = paystack_res['data']
        status = payment_data['status']
        amount_paid = float(payment_data['amount']) / 100

        transaction = Transaction.query.filter_by(reference=reference).first()
        if not transaction:
            return jsonify({'status': 'failed', 'error': 'Reason...'}), 400



        if status == 'success' and transaction.status != 'success':
            transaction.amount = amount_paid  # Update with actual paid amount
            transaction.status = 'success'
            db.session.commit()

            wallet = Wallet.query.get(transaction.wallet_id)
            if not wallet:
                return jsonify({'error': 'Wallet not found'}), 404

            wallet.balance += transaction.amount  # Now it's safe
            db.session.commit()



            return jsonify({
                'status': 'success',
                'message': 'Payment verified successfully',
                'transaction': {
                    'amount': float(transaction.amount),
                    'status': transaction.status,
                    'reference': transaction.reference
                }
            }), 200


    except Exception as e:
        return jsonify({'error': 'Server error', 'message': str(e)}), 500
