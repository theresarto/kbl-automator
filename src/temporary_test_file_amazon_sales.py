# Debug script to check what we're missing
import pandas as pd

# Read the raw Amazon CSV
df = pd.read_csv('data/input/Amazon_Sales_2024Sep-2025Sep.csv', skiprows=7)

# Filter to January 2025
df['date/time'] = pd.to_datetime(df['date/time'], utc=True)
january_df = df[(df['date/time'] >= '2025-01-01') & (df['date/time'] < '2025-02-01')]

print(f"Total January transactions: {len(january_df)}")
print(f"\nTransaction types in January:")
print(january_df['type'].value_counts())

# Sum by type
print("\nTotal amounts by type:")
for t in january_df['type'].unique():
    type_df = january_df[january_df['type'] == t]
    total = type_df['total'].sum()
    print(f"{t}: £{total:.2f}")

# Check what we're filtering out
has_order_id = january_df[january_df['order id'].notna() & (january_df['order id'] != '')]
no_order_id = january_df[january_df['order id'].isna() | (january_df['order id'] == '')]

print(f"\nTransactions with order ID: {len(has_order_id)} (Total: £{has_order_id['total'].sum():.2f})")
print(f"Transactions without order ID: {len(no_order_id)} (Total: £{no_order_id['total'].sum():.2f})")