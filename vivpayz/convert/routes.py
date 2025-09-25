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
    from_currency = data.get('base_currency')
    to_currency = data.get('target_currency')
    amount = Decimal(str(data.get('amount', 0)))

    if not from_currency or not to_currency:
        return jsonify({'error': 'Missing base or target currency'}), 400

    rate = ExchangeRate.query.filter_by(
        base_currency=from_currency, target_currency=to_currency
    ).first()

    if not rate:
        return jsonify({'error': 'Rate not available'}), 404

    effective_rate = Decimal(str(rate.rate)) * Decimal("0.95")  # 5% markup
    base_amount = amount * effective_rate

    # Service fee (percent + cap from env or default)
    fee_percent = Decimal(os.getenv("SERVICE_FEE_PERCENT", "0.01"))
    fee_cap = Decimal(os.getenv("SERVICE_FEE_CAP", "2000.00"))
    service_fee = min(base_amount * fee_percent, fee_cap)

    final_estimate = (base_amount - service_fee).quantize(Decimal("0.01"))

    return jsonify({
        "effective_rate": float(effective_rate),
        "service_fee": float(service_fee),
        "estimated_final": float(final_estimate)
    }), 200
