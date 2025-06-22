from flask import Blueprint, request, jsonify
from vivpayz.models import db, Transaction
import hashlib
import hmac
import json
import os

webhook_bp = Blueprint('webhook', __name__, url_prefix='/api')

@webhook_bp.route('/paystack/webhook', methods=['POST'])
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

