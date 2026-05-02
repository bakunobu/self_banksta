# Local CSV Client

A lightweight financial calculator for generating monthly payment schedules, estimating compound interest, and simulating recurring deposit returns. Built with Python and Pandas for simple data handling and export-ready reporting.

Perfect for personal finance planning, loan estimation, or educational use — all without external dependencies or cloud services.

---

## 🎯 Features

- 🔢 **Calculate compound interest** summaries (total paid, interest, duration)
- 📅 **Generate monthly payment schedules** with dates and amounts
- 💰 **Simulate recurring deposits** to estimate long-term savings growth
- ⚙️ **Store configuration in JSON** for persistent client settings
- 📥 **Export results to CSV or DataFrame** for further analysis
- 🌐 **Fetch actual key interest rate** from Central Bank of Russia API
- 🧮 **Calculate actual rate** based on current economic conditions
- 🤖 **Run as a Telegram bot** for convenient access from any device

---

## 📁 Project Structure
project_root/<br>
├── example.py                    # Example usage of financial functions<br>
├── local_csv_client.py         # Main script with financial functions and CBR API integration<br>
├── ui.py                          # Interactive command-line interface<br>
├── telegram_loan_bot/           # Telegram bot implementation<br>
├── config.json                   # Auto-generated config file (on first run)<br>
└── output/<br>
└── payment_schedule.csv    # Example export (optional)<br>

---

## 🛠️ Setup

1. Clone or create the project directory.
2. Install required dependencies:

```bash
pip install -r requirements.txt
```

## 📈 Key Functions

### Financial Calculations

**calculate_compound_interest(principal, rate, years, compounds_per_year=12)**
Returns a dictionary with:
- Total amount
- Total interest
- Effective annual rate (APY)

**generate_monthly_payment_schedule(principal, annual_rate, months)**
Generates a Pandas DataFrame with:
- payment_number
- payment_date (starting from next month)
- payment_amount (fixed monthly)

**calculate_deposit_effect(principal, num_months, annual_rate)**
Estimates future value of a deposit with monthly contributions using compound interest.
Returns:
- Final balance
- Total contributions
- Total interest earned

### Configuration Management

**load_config(data_path:str)**
Loads configuration from JSON file.

**update_config(data_path:str, config:dict)**
Saves configuration to JSON file.

### API Integration

**CBRClient**
Class for fetching key interest rate from Central Bank of Russia API.

**calculate_actual_rate()**
Fetches current key interest rate and returns a realistic annual rate for calculations.

## 🚀 Usage

### Command Line Interface

Run the interactive interface:

```bash
python ui.py
```

### Telegram Bot

The application can be run as a Telegram bot for convenient access from any device:

1. Set up your bot token in the configuration file
2. Run the Telegram bot:

```bash
python telegram_loan_bot/bot.py
```

The bot provides the same functionality as the command-line interface with a user-friendly chat interface.

### Direct Usage

Use the functions directly in your code:

```python
from local_csv_client import calculate_deposit_effect
print(calculate_deposit_effect(5500, 6, 0.18))
```

## 📄 License
MIT License

See LICENSE for details.