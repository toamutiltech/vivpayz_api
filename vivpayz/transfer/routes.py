from flask import Blueprint, request, jsonify
from vivpayz.utils.auth import token_required
from vivpayz.models import db, Wallet, Transfer, Transaction
import uuid
import requests
import hashlib
import hmac
import json
import os

transfer_bp = Blueprint('transfer', __name__, url_prefix='/api')

PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY')

def create_paystack_recipient(name, account_number, bank_code):
    url = "https://api.paystack.co/transferrecipient"
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "type": "nuban",
        "name": name,
        "account_number": account_number,
        "bank_code": bank_code,
        "currency": "NGN"
    }

    res = requests.post(url, headers=headers, json=data)
    res_data = res.json()
    if res_data.get("status"):
        return res_data["data"]["recipient_code"]
    else:
        raise Exception("Failed to create recipient: " + res_data.get("message", "Unknown error"))

def initiate_paystack_transfer(amount, recipient_code, reason, reference):
    url = "https://api.paystack.co/transfer"
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "source": "balance",
        "amount": int(amount * 100),  # Convert to kobo
        "recipient": recipient_code,
        "reason": reason,
        "reference": reference
    }

    res = requests.post(url, headers=headers, json=data)
    res_data = res.json()
    if res_data.get("status"):
        return res_data["data"]
    else:
        raise Exception("Transfer failed: " + res_data.get("message", "Unknown error"))


@transfer_bp.route('/paystack/transfer', methods=['POST'])
@token_required
def paystack_transfer(current_user):
    data = request.get_json()
    amount = data.get('amount')
    account_number = data.get('account_number')
    bank_code = data.get('bank_code')
    recipient_name = data.get('recipient_name')

    # Validate inputs
    if not all([amount, account_number, bank_code, recipient_name]):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError("Amount must be greater than zero")
    except ValueError:
        return jsonify({'error': 'Invalid amount format'}), 400

    # Check wallet
    wallet = Wallet.query.filter_by(user_id=current_user.id, currency='NGN').first()
    if not wallet:
        return jsonify({'error': 'NGN wallet not found'}), 404

    if wallet.balance < amount:
        return jsonify({'error': 'Insufficient NGN balance'}), 400

    try:
        # 1. Create recipient in Paystack
        recipient_code = create_paystack_recipient(recipient_name, account_number, bank_code)

        # 2. Generate reference
        reference = f"TRF_{uuid.uuid4().hex[:10]}"

        # 3. Initiate transfer
        transfer_response = initiate_paystack_transfer(amount, recipient_code, "User payout", reference)

        # 4. Deduct from wallet
        wallet.balance -= amount

        # 5. Log transfer
        transfer = Transfer(
            user_id=current_user.id,
            amount=amount,
            currency='NGN',
            recipient_code=recipient_code,
            recipient_name=recipient_name,
            bank_code=bank_code,
            account_number=account_number,
            reference=reference,
            status='PENDING'
        )
        db.session.add(transfer)

        # 6. Log transaction
        txn = Transaction(
            user_id=current_user.id,
            wallet_id=wallet.id,
            type='debit',
            purpose='Bank Transfer (NGN)',
            amount=amount,
            currency='NGN',
            reference=reference,
            status='success'
        )
        db.session.add(txn)

        db.session.commit()

        return jsonify({
            'message': 'Transfer initiated successfully',
            'transfer': transfer_response,
            'new_balance': float(wallet.balance),
            'reference': reference
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Transfer failed', 'details': str(e)}), 500
    
@transfer_bp.route('/paystack/banks', methods=['GET'])
def get_banks():
    headers = {
        "Authorization": f"Bearer {os.getenv('PAYSTACK_SECRET_KEY')}"
    }
    res = requests.get("https://api.paystack.co/bank?currency=NGN", headers=headers)
    return jsonify(res.json()), res.status_code


@transfer_bp.route('/paystack/mobile-money-transfer', methods=['POST'])
@token_required
def send_mobile_money(current_user):
    data = request.get_json()
    name = data.get('name')
    phone = data.get('phone')
    amount = data.get('amount')
    currency = data.get('currency', 'XOF')

    if not all([name, phone, amount]):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError("Amount must be greater than zero")
    except ValueError:
        return jsonify({'error': 'Invalid amount format'}), 400

    # 1. Check user wallet
    wallet = Wallet.query.filter_by(user_id=current_user.id, currency=currency).first()
    if not wallet:
        return jsonify({'error': f'{currency} wallet not found'}), 404

    if wallet.balance < amount:
        return jsonify({'error': 'Insufficient wallet balance'}), 400

    try:
        headers = {
            "Authorization": f"Bearer {os.getenv('PAYSTACK_SECRET_KEY')}",
            "Content-Type": "application/json"
        }

        # 2. Create transfer recipient
        recipient_payload = {
            "type": "mobile_money",
            "name": name,
            "account_number": phone,
            "bank_code": "MOBILEMONEY",  # Paystack-required
            "currency": currency
        }

        recipient_res = requests.post(
            "https://api.paystack.co/transferrecipient",
            headers=headers,
            json=recipient_payload
        )

        if recipient_res.status_code != 200:
            return jsonify({'error': 'Recipient creation failed', 'details': recipient_res.json()}), 400

        recipient_code = recipient_res.json()['data']['recipient_code']

        # 3. Generate reference
        reference = f"MOMO_{uuid.uuid4().hex[:10]}"

        # 4. Initiate transfer
        transfer_payload = {
            "source": "balance",
            "amount": int(amount * 100),  # Convert to centime
            "recipient": recipient_code,
            "reason": "Mobile Money Transfer",
            "reference": reference
        }

        transfer_res = requests.post(
            "https://api.paystack.co/transfer",
            headers=headers,
            json=transfer_payload
        )

        if transfer_res.status_code != 200:
            return jsonify({'error': 'Transfer initiation failed', 'details': transfer_res.json()}), 400

        # 5. Deduct from wallet
        wallet.balance -= amount

        # 6. Log to Transfer table
        transfer = Transfer(
            user_id=current_user.id,
            amount=amount,
            currency=currency,
            recipient_code=recipient_code,
            recipient_name=name,
            account_number=phone,
            bank_code="MOBILEMONEY",
            reference=reference,
            status='PENDING'
        )
        db.session.add(transfer)

        # 7. Log to Transactions table
        txn = Transaction(
            user_id=current_user.id,
            wallet_id=wallet.id,
            type='debit',
            purpose='Mobile Money Transfer',
            amount=amount,
            currency=currency,
            reference=reference,
            status='success'
        )
        db.session.add(txn)

        db.session.commit()

        return jsonify({
            'message': 'Mobile money transfer initiated',
            'reference': reference,
            'transfer_data': transfer_res.json()['data'],
            'new_balance': float(wallet.balance)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Transfer failed', 'details': str(e)}), 500
    
@transfer_bp.route('/transactions', methods=['GET'])
@token_required
def get_transactions(current_user):
    txns = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.created_at.desc()).all()
    result = [{
        'id': txn.id,
        'purpose': txn.purpose,
        'amount': float(txn.amount),
        'currency': txn.currency,
        'reference': txn.reference,
        'status': txn.status,
        'type': txn.type,
        'created_at': txn.created_at.isoformat()
    } for txn in txns]
    return jsonify({'transactions': result})


@transfer_bp.route('/paystack/webhook', methods=['POST'])
def paystack_webhook():
    secret = os.getenv("PAYSTACK_SECRET_KEY")
    signature = request.headers.get('x-paystack-signature')
    payload = request.data

    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha512
    ).hexdigest()

    if signature != expected_signature:
        return jsonify({'error': 'Invalid signature'}), 401

    event = json.loads(payload)
    event_type = event.get('event')

    if event_type == 'transfer.success':
        reference = event['data']['reference']
        transaction = Transaction.query.filter_by(reference=reference).first()
        if transaction:
            transaction.status = 'success'
            db.session.commit()

    return '', 200

