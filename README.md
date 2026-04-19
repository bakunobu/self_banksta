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

---

## 📁 Project Structure
project_root/
├── utils.py    # Main script with financial functions
├── config.json            # Auto-generated config file (on first run)
└── output/
└── payment_schedule.csv  # Example export (optional)

---

## 🛠️ Setup

1. Clone or create the project directory.
2. Install required dependencies:

```bash
pip install -r requirements.txt
```

📈 Key Functions
calculate_compound_interest(principal, rate, years, compounds_per_year=12)
Returns a dictionary with:

Total amount
Total interest
Effective annual rate (APY)
generate_monthly_payment_schedule(principal, annual_rate, months)
Generates a Pandas DataFrame with:

payment_number
payment_date (starting from next month)
payment_amount (fixed monthly)
Ideal for reports or exporting to CSV.

calculate_deposit_effect(initial, monthly_deposit, annual_rate, years)
Estimates future value of recurring deposits using compound interest.

Returns:

Final balance
Total contributions
Total interest earned

📄 License
MIT License

See LICENSE for details.