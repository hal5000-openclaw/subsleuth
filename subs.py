import csv
import argparse
import json
from datetime import datetime, timedelta
from collections import defaultdict
import re
import sys

def parse_csv(file_path):
    """Parse CSV file and return transactions with detected columns."""
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        # Detect columns by common names
        date_col = next((col for col in reader.fieldnames if col.lower() in ['date', 'transaction_date', 'posting_date']), None)
        merchant_col = next((col for col in reader.fieldnames if col.lower() in ['merchant', 'description', 'name']), None)
        amount_col = next((col for col in reader.fieldnames if col.lower() in ['amount', 'debit', 'charge']), None)

        if not all([date_col, merchant_col, amount_col]):
            raise ValueError("Could not detect required columns in CSV")

        transactions = []
        for row in reader:
            try:
                date = datetime.strptime(row[date_col], '%Y-%m-%d').date()
            except ValueError:
                try:
                    date = datetime.strptime(row[date_col], '%m/%d/%Y').date()
                except ValueError:
                    raise ValueError(f"Could not parse date: {row[date_col]}")

            amount = float(row[amount_col])
            # Treat debit as positive cost
            if amount < 0:
                amount = abs(amount)

            transactions.append({
                'date': date,
                'merchant': row[merchant_col],
                'amount': amount,
                'original_merchant': row[merchant_col]
            })

    return transactions

def normalize_merchant(name):
    """Normalize merchant name for comparison."""
    # Lowercase, remove punctuation, collapse whitespace
    name = name.lower()
    name = re.sub(r'[^a-z0-9 ]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def detect_recurring(transactions):
    """Detect recurring transactions and classify their cadence."""
    merchant_groups = defaultdict(list)

    # Group by normalized merchant and amount
    for tx in transactions:
        normalized = normalize_merchant(tx['merchant'])
        merchant_groups[(normalized, tx['amount'])].append(tx)

    recurring = []

    for (normalized, amount), txs in merchant_groups.items():
        if len(txs) < 2:
            continue

        # Calculate intervals between transactions
        txs_sorted = sorted(txs, key=lambda x: x['date'])
        intervals = [
            (txs_sorted[i+1]['date'] - txs_sorted[i]['date']).days
            for i in range(len(txs_sorted)-1)
        ]

        if not intervals:
            continue

        median_interval = sorted(intervals)[len(intervals)//2]

        # Classify cadence
        if 25 <= median_interval <= 38:  # Monthly ±3 days
            cadence = 'monthly'
        elif 340 <= median_interval <= 390:  # Annual ±10 days
            cadence = 'annual'
        else:
            continue

        # Check amount stability
        amounts = [tx['amount'] for tx in txs]
        if max(amounts) - min(amounts) > 0.01:
            continue

        first_date = min(tx['date'] for tx in txs)
        last_date = max(tx['date'] for tx in txs)

        recurring.append({
            'merchant': txs[0]['original_merchant'],
            'cadence': cadence,
            'amount': amount,
            'occurrences': len(txs),
            'first_date': first_date,
            'last_date': last_date,
            'monthly_cost': amount if cadence == 'monthly' else amount / 12,
            'annual_cost': amount if cadence == 'annual' else amount * 12
        })

    return recurring

def format_output(recurring, output_format='table'):
    """Format output as table or JSON."""
    if output_format == 'json':
        return json.dumps(recurring, indent=2, default=str)

    # Table output
    output = []
    output.append("Recurring Subscriptions:")
    output.append("""\n{:<30} {:<10} {:<10} {:<12} {:<12} {:<12} {:<12}""".format(
        "Merchant", "Cadence", "Amount", "Occurrences", "First Date", "Last Date", "Monthly Cost"))
    output.append("-" * 100)

    total_monthly = 0
    total_annual = 0

    for sub in recurring:
        output.append("""{:<30} {:<10} {:<10.2f} {:<12} {:<12} {:<12} {:<12.2f}""".format(
            sub['merchant'], sub['cadence'], sub['amount'], sub['occurrences'],
            sub['first_date'], sub['last_date'], sub['monthly_cost']))
        total_monthly += sub['monthly_cost']
        total_annual += sub['annual_cost']

    output.append("-" * 100)
    output.append(f"Total Monthly Cost: {total_monthly:.2f}")
    output.append(f"Total Annual Cost: {total_annual:.2f}")

    return '\n'.join(output)

def main():
    parser = argparse.ArgumentParser(description='Subscription cost tracker from bank CSV')
    parser.add_argument('csv_file', help='Path to bank CSV file')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    args = parser.parse_args()

    try:
        transactions = parse_csv(args.csv_file)
        recurring = detect_recurring(transactions)
        output_format = 'json' if args.json else 'table'
        print(format_output(recurring, output_format))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()