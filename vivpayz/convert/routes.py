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

        # -------------------------
        # Apply conversion logic
        # -------------------------

        # 1. Effective rate (5% markup included)
        effective_rate = Decimal(str(rate.rate)) * Decimal("0.95")

        # 2. Base converted amount using effective rate
        base_amount = from_amount * effective_rate  

        # 3. Tiered service fee (explicit to user)
        # -------------------------
        # Service Fee Calculation (percentage + cap)
        # -------------------------
        percentage_fee = from_amount * Decimal("0.01")  # 1% of original amount
        max_fee = Decimal("2000.00")  # Maximum fee cap

        service_fee = min(percentage_fee, max_fee)

        # Final amount after service fee
        to_amount = (base_amount - service_fee).quantize(Decimal("0.01"))


        # -------------------------
        # Wallet checks
        # -------------------------
        from_wallet = Wallet.query.filter_by(user_id=current_user.id, currency=from_currency).first()
        to_wallet = Wallet.query.filter_by(user_id=current_user.id, currency=to_currency).first()

        if not from_wallet or not to_wallet:
            return jsonify({'error': 'Wallet(s) not found'}), 404

        if from_wallet.balance < from_amount:
            return jsonify({'error': 'Insufficient balance in source wallet'}), 400

        # -------------------------
        # Perform wallet updates
        # -------------------------
        from_wallet.balance -= from_amount
        to_wallet.balance += to_amount

        # Log the conversion
        conversion = CurrencyConversion(
            user_id=current_user.id,
            from_currency=from_currency,
            to_currency=to_currency,
            from_amount=from_amount,
            rate=effective_rate,  # ✅ store effective rate
            to_amount=to_amount,
            status='SUCCESS'
        )
        db.session.add(conversion)

        # Record transaction
        reference = str(uuid.uuid4())
        txn = Transaction(
            user_id=current_user.id,
            wallet_id=to_wallet.id,
            type='credit',
            purpose=f'Currency converted {to_currency} Wallet Funded',
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
            'to_amount': float(to_amount),
            'effective_rate': float(effective_rate),  # ✅ send effective rate to frontend
            'service_fee': float(service_fee)         # ✅ transparent to user
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Conversion failed', 'details': str(e)}), 500





@convert_bp.route('/preview-conversion', methods=['POST'])
@token_required
def preview_conversion(current_user):
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

        # ✅ Apply 5% markup
        adjusted_rate = Decimal(str(rate.rate)) * Decimal("0.95")

        # Base converted amount
        base_amount = from_amount * adjusted_rate

        # Tiered service fee (same as /convert-currency)
        # -------------------------
        # Service Fee Calculation (percentage + cap)
        # -------------------------
        percentage_fee = from_amount * Decimal("0.01")  # 1% of original amount
        max_fee = Decimal("2000.00")  # Maximum fee cap

        service_fee = min(percentage_fee, max_fee)

        # Final amount after service fee
        to_amount = (base_amount - service_fee).quantize(Decimal("0.01"))


        return jsonify({
            'from_currency': from_currency,
            'to_currency': to_currency,
            'from_amount': float(from_amount),
            'rate': float(adjusted_rate),     # user sees adjusted rate
            'converted_before_fee': float(base_amount),
            'service_fee': float(service_fee),
            'final_amount': float(to_amount)  # ✅ what user will actually get
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
