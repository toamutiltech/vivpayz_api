from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.exc import SQLAlchemyError
from vivpayz.models import db, User, Wallet, ExchangeRate, CurrencyConversion, Transaction
from vivpayz.utils.auth import token_required
from decimal import Decimal
import uuid


convert_bp = Blueprint('convert', __name__, url_prefix='/api')

@convert_bp.route('/convert-currency', methods=['POST'])
@token_required
def convert_currency(current_user):
    data = request.get_json()
    from_currency = data.get('from_currency')
    to_currency = data.get('to_currency')
    from_amount = Decimal(str(data.get('amount', 0)))

    if not from_currency or not to_currency or from_amount <= 0:
        return jsonify({'error': 'Invalid conversion data'}), 400

    if from_currency == to_currency:
        return jsonify({'error': 'Cannot convert to the same currency'}), 400

    try:
        rate = ExchangeRate.query.filter_by(
            base_currency=from_currency,
            target_currency=to_currency
        ).first()

        if not rate:
            return jsonify({'error': 'Exchange rate not available'}), 400

        to_amount = (from_amount * Decimal(str(rate.rate))).quantize(Decimal("0.01"))

        from_wallet = Wallet.query.filter_by(user_id=current_user.id, currency=from_currency).first()
        to_wallet = Wallet.query.filter_by(user_id=current_user.id, currency=to_currency).first()

        if not from_wallet or not to_wallet:
            return jsonify({'error': 'Wallet(s) not found'}), 404

        if from_wallet.balance < from_amount:
            return jsonify({'error': 'Insufficient balance in source wallet'}), 400

        # Perform wallet updates
        from_wallet.balance -= from_amount
        to_wallet.balance += to_amount

        # Log the conversion
        conversion = CurrencyConversion(
            user_id=current_user.id,
            from_currency=from_currency,
            to_currency=to_currency,
            from_amount=from_amount,
            rate=rate.rate,
            to_amount=to_amount,
            status='SUCCESS'
        )

        db.session.add(conversion)

        reference = str(uuid.uuid4())
        txn = Transaction(
            user_id=current_user.id,
            wallet_id=to_wallet.id,
            type='credit',
            purpose='Currency converted CFA Wallet Funded',
            amount=to_amount,
            currency=to_currency,
            reference=reference,
            status='success'
        )
        db.session.add(txn)
        db.session.commit()

        return jsonify({
            'message': 'Currency converted successfully',
            'conversion_id': conversion.id,
            'from_balance': float(from_wallet.balance),
            'to_balance': float(to_wallet.balance),
            'to_amount': float(to_amount)
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Conversion failed', 'details': str(e)}), 500
