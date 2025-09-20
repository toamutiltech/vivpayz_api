from flask import request, jsonify, render_template, Blueprint
from datetime import datetime
from vivpayz.models import db
from vivpayz.models import ContactMessage, User, NewsletterSubscriber, ExchangeRate
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError
import smtplib
from email.mime.text import MIMEText
import re
import os



main = Blueprint('main', __name__)

@main.route("/")
@main.route("/home")
def home():
    return render_template("home.html")


@main.route("/contact", methods=["POST"])
def contact():
    try:
        # Handle JSON or FormData
        data = request.get_json(silent=True) or request.form

        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        message = data.get("message", "").strip()

        # Basic validation
        if not name or not email or not message:
            return jsonify({"error": "All fields are required."}), 400

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return jsonify({"error": "Invalid email address."}), 400

        # Save to database
        new_msg = ContactMessage(
            name=name,
            email=email,
            message=message,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.session.add(new_msg)
        db.session.commit()

        # Send email notification
        try:
            subject = f"New Contact Message from {name}"
            body = f"""
                <strong>Name:</strong> {name}<br>
                <strong>Email:</strong> {email}<br>
                <strong>Message:</strong><br>{message}
            """

            msg = MIMEText(body, "html")
            msg["Subject"] = subject
            msg["From"] = os.getenv("SMTP_FROM")
            msg["To"] = os.getenv("SMTP_TO")

            with smtplib.SMTP(os.getenv("SMTP_SERVER"), int(os.getenv("SMTP_PORT"))) as server:
                server.starttls()
                server.login(os.getenv("SMTP_USERNAME"), os.getenv("SMTP_PASSWORD"))
                server.sendmail(msg["From"], [msg["To"]], msg.as_string())

        except Exception as mail_err:
            return jsonify({
                "warning": f"Message saved but email failed: {str(mail_err)}"
            }), 202

        return jsonify({
            "success": "Thank you! Your message has been received."
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@main.route("/waitlist", methods=["POST"])
def waitlist():
    try:
        data = request.get_json(silent=True) or request.form

        fname = data.get("fname", "").strip()
        email = data.get("email", "").strip().lower()
        country = data.get("country", "").strip()

        # Validation
        if not fname or not email or not country:
            return jsonify({"error": "All fields are required."}), 400
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return jsonify({"error": "Invalid email format."}), 400

        # Generate password & referral code
        hashed_password = generate_password_hash("vivpayz123")
        refer_code = os.urandom(6).hex().upper()

        # Create user
        new_user = User(
            email=email,
            password=hashed_password,
            fname=fname,
            lname="",
            refercode=refer_code,
            phone="",
            is_verified=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        db.session.add(new_user)
        db.session.commit()

        # Send confirmation email
        try:
            subject = "Vivpayz Waitlist Confirmation"
            body = f"""
            <h2>🎉 Thank you for joining the Vivpayz Waitlist!</h2>
            <p>Hi {fname},</p>
            <p>We’re excited to have you on board.</p>
            <p><strong>Your Referral Code:</strong> {refer_code}</p>
            <p><strong>Your Password:</strong> vivpayz123</p>
            <p>We'll notify you once the app goes live.</p>
            <br><em>- The Vivpayz Team</em>
            """

            msg = MIMEText(body, "html")
            msg["Subject"] = subject
            msg["From"] = os.getenv("SMTP_FROM")
            msg["To"] = email

            with smtplib.SMTP(os.getenv("SMTP_SERVER"), int(os.getenv("SMTP_PORT"))) as server:
                server.starttls()
                server.login(os.getenv("SMTP_USERNAME"), os.getenv("SMTP_PASSWORD"))
                server.sendmail(msg["From"], [msg["To"]], msg.as_string())

        except Exception as mail_err:
            return jsonify({"warning": f"User saved but email failed: {mail_err}"}), 202

        return jsonify({"success": "You're now on the waitlist! Please check your email for confirmation."}), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "This email is already on the waitlist."}), 409

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    

@main.route("/newsletter", methods=["POST"])
def subscribe():
    data = request.get_json()
    email = data.get("email", "").strip()

    if not email or "@" not in email:
        return jsonify({"status": "error", "message": "Invalid email address."}), 400

    existing = NewsletterSubscriber.query.filter_by(email=email).first()
    if existing:
        return jsonify({"status": "info", "message": "Email is already subscribed."})

    new_sub = NewsletterSubscriber(email=email)
    db.session.add(new_sub)
    db.session.commit()

    return jsonify({"status": "success", "message": "Thank you for subscribing!"})


@main.route("/api/update-rates", methods=["POST"])
def update_rates():
    try:
        data = request.get_json()

        base = data.get("base_currency")
        target = data.get("target_currency")
        rate = data.get("rate")

        if not base or not target or not rate:
            return jsonify({"error": "Missing fields"}), 400

        # Upsert logic (insert or update if exists)
        existing = ExchangeRate.query.filter_by(base_currency=base, target_currency=target).first()

        if existing:
            existing.rate = rate
            existing.updated_at = datetime.utcnow()
        else:
            new_rate = ExchangeRate(
                base_currency=base,
                target_currency=target,
                rate=rate,
            )
            db.session.add(new_rate)

        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"Rate updated {base} -> {target}: {rate}"
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500