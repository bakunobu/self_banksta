# Local CSV Client

A lightweight financial calculator for generating monthly payment schedules, estimating interest, and simulating deposit returns. Designed for local execution and simple reporting via Pandas DataFrames.

## 🎯 Features

- Calculate compound interest summaries
- Generate payment schedules with dates and amounts
- Simulate interest accumulation from recurring deposits
- Store client configuration in JSON
- Export-ready outputs (can be saved to CSV)

## 📁 Structure

project_root/
├── local_csv_client.py        # Main script
└── data/
└── config.json            # Auto-generated config

## 🛠️ Setup

Ensure dependencies are installed:

```bash
pip install pandas
```

📈 Functions
calculate_compound_interest(...)
Returns a summary dictionary of loan/interest details.

generate_monthly_payment_schedule(...)
Creates a Pandas DataFrame with:

payment_number
payment_date
payment_amount
Ideal for exporting to reports or CSV.

calculate_deposit_effect(...)
Estimates total interest gained by repeatedly investing a fixed amount monthly.

⚠️ Known Limitations

No input validation (e.g., negative values, invalid dates).

Does not break down principal vs interest per payment.


💡 Example Output
   payment_number payment_date  payment_amount
0               1   2026-05-01      95833.33
1               2   2026-06-01      95833.33
...
📄 License
MIT (or specify yours)


---

Let me know if you'd like:
- A corrected version of `calculate_compound_interest()` using proper amortization
- CSV export functionality
- Principal/interest breakdown per payment
- Unit tests

I'm happy to help improve the codebase!