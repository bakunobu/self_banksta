import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Go up to root
sys.path.append(ROOT_DIR)  # Add data directory to sys.path for importing

import sqlite3
import logging
import asyncio
import pandas as pd
from io import BytesIO
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from local_csv_client import ParseKeyRates
from weasyprint import HTML, CSS

# Load environment variables
load_dotenv()
TOKEN = os.environ.get('TOKEN_TG', 'YOUR_BOT_TOKEN_HERE')

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ==========================================
# 1. DATABASE & CONFIGURATION LOGIC
# ==========================================
DATA_DIR = os.path.join(ROOT_DIR, "data")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# File paths
DB_FILE = os.path.join(DATA_DIR, "loan_bot.db")
CONFIG_JSON = os.path.join(DATA_DIR, "config.json")  # In case you still use it
BASE_KEY_RATE = ParseKeyRates().return_actual_rate()[1]  # Example base rate (16%). You can update this as needed.


def init_db():
    """Initializes a local SQLite database to store user spreads."""
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                spread REAL DEFAULT 0.0
            )
        ''')

def get_user_spread(user_id: int) -> float:
    """Fetches the custom spread for a specific user."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT spread FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        return row[0] if row else 0.0

def set_user_spread(user_id: int, username: str, spread: float):
    """Saves a custom spread for a specific user."""
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''
            INSERT INTO users (user_id, username, spread)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET spread=excluded.spread, username=excluded.username
        ''', (user_id, username, spread))

# ==========================================
# 2. FINANCIAL CALCULATION LOGIC
# ==========================================
def generate_pdf_report(total: dict, df: pd.DataFrame, user_id: int) -> bytes:
    """
    Generate a PDF report from loan calculation data.
    
    Args:
        total (dict): The loan summary data from calculate_compound_interest
        df (pd.DataFrame): The payment schedule
        user_id (int): The user's ID for temporary file naming
    
    Returns:
        bytes: The PDF content as bytes
    """
    # Create HTML content for the PDF
    html_content = f'''
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 2cm; }}
            h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            h2 {{ color: #2980b9; margin-top: 20px; }}
            .summary {{ 
                background-color: #f8f9fa; 
                padding: 15px; 
                border-radius: 5px; 
                margin: 15px 0; 
                border-left: 4px solid #3498db; 
            }}
            table {{ 
                width: 100%; 
                border-collapse: collapse; 
                margin: 15px 0; 
            }}
            th, td {{ 
                border: 1px solid #ddd; 
                padding: 8px; 
                text-align: left; 
            }}
            th {{ 
                background-color: #f2f2f2; 
                font-weight: bold; 
            }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .footer {{ 
                margin-top: 30px; 
                font-size: 0.8em; 
                color: #7f8c8d; 
                text-align: center; 
            }}
        </style>
    </head>
    <body>
        <h1>Loan Payment Schedule Report</h1>
        <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="summary">
            <h2>Loan Summary</h2>
            <p><strong>Principal Amount:</strong> {total['principal']:,.2f}</p>
            <p><strong>Duration:</strong> {total['duration_months']} months</p>
            <p><strong>Annual Interest Rate:</strong> {total['annual_rate']:.2%}</p>
            <p><strong>Monthly Payment:</strong> {total['monthly_payment']:,.2f}</p>
            <p><strong>Total Amount Paid:</strong> {total['total_paid']:,.2f}</p>
            <p><strong>Total Interest Paid:</strong> {total['total_interest']:,.2f}</p>
            <p><strong>Deposit Effect:</strong> {total['deposit_effect']:,.2f}</p>
        </div>
        
        <h2>Payment Schedule</h2>
        <table>
            <thead>
                <tr>
                    <th>Month</th>
                    <th>Payment</th>
                    <th>Principal</th>
                    <th>Interest</th>
                    <th>Remaining Balance</th>
                </tr>
            </thead>
            <tbody>'''}
    
    # Add table rows
    for _, row in df.iterrows():
        html_content += f'''
                <tr>
                    <td>{int(row['Month'])}</td>
                    <td>{row['Payment']:,.2f}</td>
                    <td>{row['Principal']:,.2f}</td>
                    <td>{row['Interest']:,.2f}</td>
                    <td>{row['Remaining Balance']:,.2f}</td>
                </tr>'''
    
    # Close HTML
    html_content += f'''
            </tbody>
        </table>
        
        <div class="footer">
            <p>Loan Calculator Bot • Confidential Report</p>
        </div>
    </body>
    </html>'''
    
    # Convert HTML to PDF
    html = HTML(string=html_content)
    css = CSS(string='@page {{ size: A4; margin: 2cm }}')
    pdf_bytes = html.write_pdf(stylesheets=[css])
    
    return pdf_bytes

def calculate_compound_interest(principal: float, duration_months: int, annual_rate: float) -> dict:
    """
    Calculate compound interest and monthly payment using correct amortization formula.

    Args:
        principal (float): The initial principal amount
        duration_months (int): The duration of the investment/loan in months
        annual_rate (float): The annual interest rate as a decimal (e.g., 0.05 for 5%)

    Returns:
        dict: A dictionary containing principal, duration in months, rate,
              monthly payment, total paid, total interest, and deposit effect
    """
    monthly_rate = annual_rate / 12
    
    if monthly_rate == 0:
        monthly_payment = principal / duration_months
    else:
        monthly_payment = principal * (monthly_rate * (1 + monthly_rate)**duration_months) / ((1 + monthly_rate)**duration_months - 1)
    
    total_paid = monthly_payment * duration_months
    total_interest = total_paid - principal
    
    # Calculate deposit effect - sum of interest over time
    # This represents the total interest that would be earned if the monthly payments
    # were invested at the same rate
    deposit_effect = 0
    for i in range(duration_months):
        # For each month, calculate the interest component of the payment
        # Using the formula for interest portion of installment loan payment
        remaining_balance = principal * ((1 + monthly_rate) ** (i+1) - (1 + monthly_rate) ** i) / ((1 + monthly_rate) ** duration_months - 1)
        interest_portion = remaining_balance * monthly_rate
        deposit_effect += interest_portion

    return {
        'principal': principal,
        'duration_months': duration_months,
        'annual_rate': annual_rate,
        'monthly_payment': monthly_payment,
        'total_paid': total_paid,
        'total_interest': total_interest,
        'deposit_effect': deposit_effect
    }

def generate_monthly_payment_schedule(principal: float, duration_months: int, annual_rate: float) -> pd.DataFrame:
    monthly_rate = annual_rate / 12
    schedule = []
    balance = principal
    calc = calculate_compound_interest(principal, duration_months, annual_rate)
    monthly_payment = calc['monthly_payment']

    for month in range(1, duration_months + 1):
        interest_payment = balance * monthly_rate
        principal_payment = monthly_payment - interest_payment
        balance -= principal_payment
        
        # Handle floating point imprecision on final month
        if balance < 0.01: 
            balance = 0.0

        schedule.append({
            'Month': month,
            'Payment': round(monthly_payment, 2),
            'Principal': round(principal_payment, 2),
            'Interest': round(interest_payment, 2),
            'Remaining Balance': round(balance, 2)
        })
    
    return pd.DataFrame(schedule)

# ==========================================
# 3. TELEGRAM BOT HANDLERS
# ==========================================

def get_keyboard(include_back=False):
    """
    Returns a keyboard with main buttons.
    If include_back=True, adds a '🏠 Back to Start' button at the bottom.
    """
    keyboard = [
        [KeyboardButton("📊 Rates"), KeyboardButton("📅 Schedule")],
        [KeyboardButton("⚙️ Set Rate")]
    ]
    if include_back:
        keyboard.append([KeyboardButton("🏠 Back to Start")])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to the Loan Calculator Bot!\n"
        "Use the menu below to:\n"
        "📊 Get current interest rates\n"
        "📅 Generate payment schedules\n"
        "⚙️ Change your personal rate spread",
        reply_markup=get_keyboard()
    )
    
async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Resets state and shows the start message."""
    # Clear any pending actions (like awaiting spread)
    if 'awaiting_spread' in context.user_data:
        del context.user_data['awaiting_spread']
    
    # Re-send the start message with main keyboard
    await update.message.reply_text(
        "👋 Welcome back! What would you like to do?",
        reply_markup=get_keyboard()  # Main menu without 'Back' button
    )

async def rates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        custom_spread = get_user_spread(user_id)
        # Total actual rate = Base Key Rate + Custom Spread
        total_rate = BASE_KEY_RATE + custom_spread
        
        await update.message.reply_text(
            f"🏦 Current Interest Rates:\n"
            f"🔹 Base CB Rate: {BASE_KEY_RATE:.2%}\n"
            f"🔹 Your Bank Spread: {custom_spread:.2%}\n"
            f"📈 **Total Actual Rate:** {total_rate:.2%}",
            parse_mode="Markdown",
            reply_markup=get_keyboard(include_back=True)

        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error fetching rate: {str(e)}")

async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 To generate a payment schedule, send:\n"
        "`amount duration_months [annual_rate]`\n\n"
        "Example:\n"
        "`500000 12` (Uses your saved rate)\n"
        "`500000 12 0.17` (Forces a 17% rate)",
        parse_mode="Markdown",
        reply_markup=get_keyboard(include_back=True)
    )

async def setrate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔧 Send your new bank spread as a decimal.\n"
        "Example:\n"
        "`0.05` → adds 5% on top of key rate",
        parse_mode="Markdown",
        reply_markup=get_keyboard(include_back=True)
    )
    # Set a flag in user_data so the bot knows the next message is a spread value
    context.user_data['awaiting_spread'] = True

async def handle_setrate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        spread = float(update.message.text.strip())
        if not (0 <= spread <= 0.5):  # Max 50%
            raise ValueError("Spread must be between 0 and 0.5")

        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        # Update DB
        set_user_spread(user_id, username, spread)

        await update.message.reply_text(f"✅ Your personal bank spread has been updated to {spread:.2%}")
        
        # Clear the flag so they can use the calculator again
        context.user_data['awaiting_spread'] = False

    except ValueError:
        await update.message.reply_text("❌ Please enter a valid decimal number like `0.03`.", parse_mode="Markdown")

async def handle_loan_calculation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    try:
        parts = text.split()
        if len(parts) < 2:
            raise ValueError("Need at least amount and duration")

        principal = float(parts[0])
        duration = int(parts[1])
        
        # Use provided rate, OR fallback to base rate + user spread
        if len(parts) > 2:
            annual_rate = float(parts[2])
        else:
            user_id = update.effective_user.id
            user_spread = get_user_spread(user_id)
            annual_rate = BASE_KEY_RATE + user_spread

        # Generate schedule DataFrame
        df = generate_monthly_payment_schedule(principal, duration, annual_rate)

        # Save to CSV temporarily
        csv_file = f"schedule_{update.effective_user.id}.csv"
        df.to_csv(csv_file, index=False)

        # Get total summaries
        total = calculate_compound_interest(principal, duration, annual_rate)

        msg = (
            f"💰 *Loan Summary:*\n"
            f"Principal: `{total['principal']:,.2f}`\n"
            f"Duration: `{total['duration_months']} months`\n"
            f"Annual Rate: `{total['annual_rate']:.2%}`\n"
            f"Monthly Payment: `{total['monthly_payment']:,.2f}`\n"
            f"Total Paid: `{total['total_paid']:,.2f}`\n"
            f"Total Interest: `{total['total_interest']:,.2f}`\n\n"
            f"📎 Full schedule attached as CSV."
        )

        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=get_keyboard(include_back=True))
        
        # Send document and clean up
        with open(csv_file, 'rb') as f:
            await update.message.reply_document(document=f, filename="payment_schedule.csv")
        os.remove(csv_file)

    except Exception as e:
        await update.message.reply_text(
            "❌ Invalid input. Make sure you use numbers.\nExample: `500000 12 0.17`", 
            parse_mode="Markdown",
            reply_markup=get_keyboard(include_back=True)
        )

async def master_text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Routes plain text messages to the correct function based on user state."""
    text = update.message.text.strip()
    
    # Ignore slash commands just in case they slip through
    if text.startswith('/'):
        return

    # Route 1: User clicked "Set Rate" and is sending a new spread
    if context.user_data.get('awaiting_spread'):
        await handle_setrate(update, context)
    # Route 2: Default behavior is calculating a loan schedule
    else:
        await handle_loan_calculation(update, context)


# ==========================================
# 4. MAIN APPLICATION RUNNER
# ==========================================
if __name__ == '__main__':
    # Ensure database exists
    init_db()

    # Build the bot
    app = ApplicationBuilder().token(TOKEN).build()

    # 1. Command Handlers (/start, /rates)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^🏠 Back to Start$"), back_to_start))
    app.add_handler(CommandHandler("rates", rates))
    app.add_handler(CommandHandler("schedule", schedule))
    app.add_handler(CommandHandler("setrate", setrate))

    # 2. Button Handlers (Catching the exact text from the custom keyboard)
    app.add_handler(MessageHandler(filters.Regex("^📊 Rates$"), rates))
    app.add_handler(MessageHandler(filters.Regex("^📅 Schedule$"), schedule))
    app.add_handler(MessageHandler(filters.Regex("^⚙️ Set Rate$"), setrate))

    # 3. Master Text Router (Catches inputs like "0.05" or "50000 12")
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, master_text_router))

    print("🤖 Bot is running. Press Ctrl+C to stop.")
    app.run_polling()