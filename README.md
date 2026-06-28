# Vivpayz API

Welcome to the **Vivpayz API** repository. This is the core backend service powering the Vivpayz Fintech ecosystem, including the mobile app, web platform, and administrative dashboard. It provides secure, scalable, and comprehensive financial services.

## 🚀 Core Features

### 1. User & Identity Management
- **Authentication**: Secure JWT-based authentication with OWASP-aligned password hashing.
- **KYC Verification**: Identity verification module for regulatory compliance (`Verifications`).
- **Referral System**: Robust referral tracking (`Referral`) allowing users to invite and earn.

### 2. Digital Wallets & Transactions
- **Multi-Currency Wallets**: Users can hold and manage balances in multiple currencies (`Wallets`).
- **Transaction Ledger**: Complete immutable history for all credits, debits, and operations (`Transactions`).
- **Currency Conversion**: Real-time FX tracking (`ExchangeRate`) and cross-currency wallet swaps (`CurrencyConversion`).

### 3. Payments & Transfers
- **Fund Transfers**: Peer-to-Peer (P2P) and external bank account transfers (`Transfers`).
- **Payment Gateway**: Integration with third-party processors like **Paystack** for seamless deposits and checkouts.

### 4. Virtual & Physical Cards
- **Card Issuance**: Provision, manage, block, and track virtual/physical debit cards (`Cards`).

### 5. Utility & Bill Payments
- **Airtime & Data**: API endpoints for instant mobile network recharges (`AirtimeRecharge`, `DataRecharge`).
- **Bill Payments**: Processing for standard utilities (Electricity, TV, etc.) (`Bills`, `BillsPayment`).

## 🛠 Tech Stack & Architecture

- **Framework**: [Flask](https://flask.palletsprojects.com/) (Python)
- **Database**: PostgreSQL (hosted on Render)
- **ORM**: SQLAlchemy (`flask_sqlalchemy`)
- **Migrations**: Alembic / Flask-Migrate
- **Authentication**: `flask_jwt_extended`
- **Mail Service**: `flask_mail` (SMTP-based transactional emails)
- **Security**: Cross-Origin Resource Sharing (`flask_cors`), Werkzeug security hashes.

## 📂 Project Structure

```text
C:\flask\env_flask\vivpayz_api\
├── vivpayz/
│   ├── auth/          # Registration, Login, Password Reset
│   ├── card/          # Virtual/Physical Card management
│   ├── convert/       # Currency conversion logic
│   ├── main/          # General utility endpoints
│   ├── payment/       # Paystack & gateway webhooks
│   ├── transfer/      # P2P and external banking transfers
│   ├── user/          # Profile & KYC management
│   ├── wallet/        # Wallet balances and ledgers
│   ├── models.py      # SQLAlchemy DB schema (Users, Wallets, Transactions, etc.)
│   ├── config.py      # App configurations
│   └── __init__.py    # Flask App factory & Blueprint registration
├── migrate.py         # DB migration script
├── run.py             # Development server entry point
├── wsgi.py            # Production WSGI entry point
├── requirements.txt   # Python dependencies
└── Dockerfile         # Docker container configuration
```

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- PostgreSQL server (or use the configured Render remote DB)
- An active SMTP Server for emails
- Third-party API keys (Paystack, VTU Providers, etc.)

### Installation & Setup

1. **Clone the repository**:
   Navigate to your local directory.

2. **Set up a Virtual Environment**:
   ```bash
   python -m venv env_flask
   # Activate it (Windows)
   env_flask\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**:
   Create a `.env` file in the root directory mirroring the necessary configuration variables:
   ```env
   # Database
   SQLALCHEMY_DATABASE_URI=postgresql://user:password@host/dbname
   
   # JWT & Security
   JWT_SECRET_KEY=your_super_secret_jwt_key
   
   # SMTP Email Configuration
   SMTP_SERVER=smtp.yourprovider.com
   SMTP_PORT=587
   SMTP_USERNAME=your_email
   SMTP_PASSWORD=your_password
   SMTP_FROM=noreply@vivpayz.tech
   ```

5. **Run Database Migrations**:
   *(If you are setting up a fresh database)*
   ```bash
   flask db upgrade
   ```

6. **Run the Development Server**:
   ```bash
   python run.py
   ```
   The API will be accessible at `http://127.0.0.1:5000/`.

## 🤝 Integrations
- Cross-origin configured for frontend access from `https://vivpayz-fintech.vercel.app` and `https://vivpayz.tech`.
- File uploads are statically served from `/static/uploads/`.
