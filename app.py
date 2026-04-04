# app.py
from flask import Flask, request, jsonify
from models import Client, CreditAccount
from database import init_db
import os

app = Flask(__name__)
DB_PATH = "dbs/accounts.db"

@app.before_request
def startup():
    if not hasattr(app, 'initialized'):
        init_db()
        app.initialized = True

# ====================
# Client Endpoints
# ====================

@app.route('/clients', methods=['POST'])
def create_client():
    data = request.get_json()
    required = ['client_id', 'name', 'email']
    if not all(k in data for k in required):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        client = Client(
            client_id=data['client_id'],
            name=data['name'],
            email=data['email'],
            phone=data.get('phone', '')
        )
        return jsonify(client.to_dict()), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/clients/<client_id>', methods=['GET'])
def get_client(client_id):
    accounts = CreditAccount.get_accounts_by_client(client_id, DB_PATH)
    if not accounts:
        return jsonify({"error": "No accounts found for this client."}), 404

    client = Client(client_id=client_id, name="Unknown", email="unknown@example.com", db_path=DB_PATH)
    return jsonify(client.to_dict())

# ====================
# Account Endpoints
# ====================

@app.route('/clients/<client_id>/accounts', methods=['POST'])
def add_account(client_id):
    data = request.get_json()
    required = ['account_id', 'interest_rate', 'credit_limit']
    if not all(k in data for k in required):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        client = Client(client_id=client_id, name="Temp", email="temp@example.com", db_path=DB_PATH)
        new_acc = client.add_credit_account(
            account_id=data['account_id'],
            interest_rate=data['interest_rate'],
            credit_limit=data['credit_limit'],
            initial_amount=data.get('initial_amount', 0.0)
        )
        return jsonify(new_acc.to_dict()), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/clients/<client_id>/accounts', methods=['GET'])
def list_accounts(client_id):
    accounts = CreditAccount.get_accounts_by_client(client_id, DB_PATH)
    return jsonify([acc.to_dict() for acc in accounts])

# ====================
# Action Endpoints
# ====================

@app.route('/accounts/<account_id>/pay', methods=['POST'])
def make_payment(account_id):
    data = request.get_json()
    amount = data.get('amount')
    if not isinstance(amount, (int, float)) or amount <= 0:
        return jsonify({"error": "Valid positive amount required"}), 400

    # Find client owning this account
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT client_id FROM credit_accounts WHERE account_id = ?", (account_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Account not found"}), 404

    client = Client(client_id=row[0], name="Temp", email="temp@example.com", db_path=DB_PATH)
    result = client.make_monthly_payment(account_id, amount)
    status = 200 if "error" not in result else 400
    return jsonify(result), status

@app.route('/accounts/<account_id>/repay', methods=['POST'])
def repay_early(account_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT client_id FROM credit_accounts WHERE account_id = ?", (account_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Account not found"}), 404

    client = Client(client_id=row[0], name="Temp", email="temp@example.com", db_path=DB_PATH)
    result = client.early_repayment(account_id)
    status = 200 if "error" not in result else 400
    return jsonify(result), status

@app.route('/accounts/<account_id>/interest', methods=['POST'])
def apply_interest(account_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT client_id FROM credit_accounts WHERE account_id = ?", (account_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Account not found"}), 404

    client = Client(client_id=row[0], name="Temp", email="temp@example.com", db_path=DB_PATH)
    account = client._get_account(account_id)
    if not account:
        return jsonify({"error": "Account not loaded"}), 404

    result = account.apply_monthly_interest()
    status = 200 if "error" not in result else 400
    return jsonify(result), status

# ====================
# Health & Info
# ====================

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "db": DB_PATH})

if __name__ == '__main__':
    app.run(debug=True, port=5000)