# bot.py
import os
import sys
from pathlib import Path

parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(parent_dir)


from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackContext
import asyncio
import logging
from dotenv import load_dotenv

load_dotenv()


from local_csv_client import (
    calculate_compound_interest,
    generate_monthly_payment_schedule,
    calculate_actual_rate,
    load_config,
    update_config,
    data_path
)
from database import init_db, get_user_spread, set_user_spread
import os

TOKEN = os.environ.get('TOKEN_TG')  # ← Replace with your bot token from @BotFather

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Keyboard layout
def get_keyboard():
    keyboard = [
        [KeyboardButton("/rates"), KeyboardButton("/schedule")],
        [KeyboardButton("/setrate")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to the Loan Calculator Bot!\n"
        "Use the menu below to:\n"
        "📊 Get current interest rates\n"
        "📅 Generate payment schedules\n"
        "⚙️ Change your personal rate spread",
        reply_markup=get_keyboard()
    )

# Show current interest rate
async def rates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    custom_spread = get_user_spread(user_id)

    try:
        actual_rate_percent = calculate_actual_rate() * 100
        await update.message.reply_text(
            f"🏦 Current Key Rate + Spread:\n"
            f"🔹 Base CB Rate + Your Spread: {actual_rate_percent:.2f}%\n"
            f"🔹 Your Custom Bank Spread: {custom_spread:.2%}"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error fetching rate: {str(e)}")

# Ask for loan details to generate schedule
async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 To generate a payment schedule, send:\n"
        "`amount duration_months [annual_rate]`\n\n"
        "Example:\n"
        "`500000 12`\n"
        "`500000 12 0.17`"
    )

# Handle message input for schedule
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text.startswith('/'):
        return  # Ignore other commands

    try:
        parts = text.split()
        if len(parts) < 2:
            raise ValueError("Need at least amount and duration")

        principal = float(parts[0])
        duration = int(parts[1])
        annual_rate = float(parts[2]) if len(parts) > 2 else None

        user_id = update.effective_user.id
        user_spread = get_user_spread(user_id)

        if annual_rate is None:
            # Use calculated rate based on user's spread
            annual_rate = calculate_actual_rate()

        # Generate schedule
        df = generate_monthly_payment_schedule(principal, duration, annual_rate)

        # Save to CSV temporarily
        csv_file = f"schedule_{update.effective_user.id}.csv"
        df.to_csv(csv_file, index=False)

        total = calculate_compound_interest(principal, duration, annual_rate)

        msg = (
            f"💰 Loan Summary:\n"
            f"Principal: {total['principal']:,.2f}\n"
            f"Duration: {total['duration_months']} months\n"
            f"Annual Rate: {total['annual_rate']:.2%}\n"
            f"Monthly Payment: {total['monthly_payment']:,.2f}\n"
            f"Total Paid: {total['total_paid']:,.2f}\n"
            f"Total Interest: {total['total_interest']:,.2f}\n\n"
            f"📎 Full schedule attached as CSV."
        )

        await update.message.reply_text(msg)
        await update.message.reply_document(document=open(csv_file, 'rb'), filename="payment_schedule.csv")

        os.remove(csv_file)  # Clean up

    except Exception as e:
        await update.message.reply_text(f"❌ Invalid input. Example:\n`500000 12 0.17`", parse_mode="Markdown")

# Set custom spread
async def setrate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔧 Send your new bank spread as a decimal.\n"
        "Example:\n"
        "`0.05` → adds 5% on top of key rate"
    )
    context.user_data['awaiting_spread'] = True

async def handle_setrate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('awaiting_spread'):
        return await handle_message(update, context)  # fallback

    try:
        spread = float(update.message.text.strip())
        if not (0 <= spread <= 0.5):  # Max 50%
            raise ValueError("Spread must be between 0 and 0.5")

        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        # Update DB
        set_user_spread(user_id, username, spread)

        # Also update global config? Optional.
        config = load_config(data_path) or {}
        config['bank_spread'] = spread
        update_config(data_path, config)

        await update.message.reply_text(f"✅ Your bank spread has been updated to {spread:.2%}")
        context.user_data['awaiting_spread'] = False

    except Exception as e:
        await update.message.reply_text("❌ Please enter a valid number like `0.03`.")

# Main
if __name__ == '__main__':
    init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("rates", rates))
    app.add_handler(CommandHandler("schedule", schedule))
    app.add_handler(CommandHandler("setrate", setrate))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_setrate))  # First check setrate
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))  # Then others

    print("🤖 Bot is running...")
    app.run_polling()