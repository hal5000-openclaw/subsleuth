# Subsleuth - Subscription Cost Tracker

Detect recurring charges in bank/card CSV exports and report monthly/annual totals.

## Installation

No dependencies required - uses Python standard library only.

## Usage

```bash
python subs.py statement.csv
python subs.py statement.csv --json > subs.json
```

### CSV Format

The tool auto-detects columns by name heuristics:
- Date: `date`, `transaction_date`, `posting_date`
- Merchant: `merchant`, `description`, `name`
- Amount: `amount`, `debit`, `charge`

Date formats supported: `YYYY-MM-DD`, `MM/DD/YYYY`

### Example Output

```
Recurring Subscriptions:

Merchant                        Cadence    Amount     Occurrences  First Date   Last Date    Monthly Cost
----------------------------------------------------------------------------------------------------
Netflix                         monthly    12.99      4            2024-01-15   2024-06-01   12.99
Spotify Premium                 monthly    9.99       3            2024-01-10   2024-03-10   9.99
Amazon Prime                    annual     119.00     2            2024-01-01   2024-12-28   9.92
Annual Magazine                 annual     59.99      2            2023-06-15   2024-06-10   5.00
----------------------------------------------------------------------------------------------------
Total Monthly Cost: 37.90
Total Annual Cost: 454.80
```

### JSON Output

```json
[
  {
    "merchant": "Netflix",
    "cadence": "monthly",
    "amount": 12.99,
    "occurrences": 4,
    "first_date": "2024-01-15",
    "last_date": "2024-06-01",
    "monthly_cost": 12.99,
    "annual_cost": 155.88
  }
]
```

## Detection Rules

- Group by normalized merchant name + amount
- Require ≥2 occurrences with amount stable within $0.01
- Monthly: median interval 25-38 days
- Annual: median interval 340-390 days
- Debit transactions only (negative amounts converted to positive)
