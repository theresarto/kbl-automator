import pandas as pd
import numpy as np

# Load the files
print("Loading Excel files...")
cms_order = pd.read_excel('data/reports/Amazon_CMS_Order_Nov2024_Mar2025.xlsx', sheet_name=None)
monthly_sales = pd.read_excel('data/reports/Amazon_Monthly_Sales.xlsx', sheet_name=None)

# Get unit costs from CMS order
aggregate_df = cms_order['Aggregate_Sales']
unit_cost_mapping = {}
for _, row in aggregate_df.iterrows():
    if pd.notna(row['Items sold']) and pd.notna(row['Unit cost']):
        unit_cost_mapping[row['Items sold']] = float(row['Unit cost'])

# Check Needs_Review sheet too
if 'Needs_Review' in cms_order:
    needs_review = cms_order['Needs_Review']
    for _, row in needs_review.iterrows():
        if pd.notna(row['Items sold']) and pd.notna(row['Unit cost']):
            item = str(row['Items sold']).replace('UNMATCHED: ', '')
            unit_cost_mapping[item] = float(row['Unit cost'])

print(f"Found {len(unit_cost_mapping)} products")

# Update each monthly sheet
updated_sheets = {}
new_shipping_rate = 3.17
total_cost = 0
total_shipping = 0

for month in ['NOVEMBER_2024', 'DECEMBER_2024', 'JANUARY_2025', 'FEBRUARY_2025', 'MARCH_2025']:
    if month in monthly_sales:
        df = monthly_sales[month].copy()
        
        # Update each row
        for idx in df.index:
            if pd.notna(df.loc[idx, 'Transaction ID']) and df.loc[idx, 'Transaction ID'] not in ['Total', '']:
                item = df.loc[idx, 'Items sold']
                
                # Update cost from mapping
                if item in unit_cost_mapping and item != 'AMAZON SUBSCRIPTION FEE':
                    qty = float(df.loc[idx, 'Quantity'])
                    unit_cost = unit_cost_mapping[item]
                    df.loc[idx, 'Cost price'] = unit_cost * qty
                    df.loc[idx, 'COST LESS VAT'] = (unit_cost * qty) / 1.2
                
                # Update shipping
                if df.loc[idx, 'Shipping cost'] == 3.21:
                    df.loc[idx, 'Shipping cost'] = new_shipping_rate
                
                # Recalculate profit
                if item != 'AMAZON SUBSCRIPTION FEE':
                    df.loc[idx, 'NET PROFIT'] = (df.loc[idx, 'Sold for'] - 
                                                df.loc[idx, 'Amazon fees'] - 
                                                df.loc[idx, 'Shipping cost'] - 
                                                df.loc[idx, 'Cost price'])
        
        # Update totals
        data_rows = df[(df['Transaction ID'] != 'Total') & (df['Transaction ID'] != '')]
        if any(df['Transaction ID'] == 'Total'):
            idx = df[df['Transaction ID'] == 'Total'].index[0]
            df.loc[idx, 'Quantity'] = data_rows['Quantity'].sum()
            df.loc[idx, 'Sold for'] = data_rows['Sold for'].sum()
            df.loc[idx, 'Shipping cost'] = data_rows['Shipping cost'].sum()
            df.loc[idx, 'Amazon fees'] = data_rows['Amazon fees'].sum()
            df.loc[idx, 'Cost price'] = data_rows['Cost price'].sum()
            df.loc[idx, 'COST LESS VAT'] = data_rows['COST LESS VAT'].sum()
            df.loc[idx, 'NET PROFIT'] = data_rows['NET PROFIT'].sum()
        
        updated_sheets[month] = df
        
        # Track totals
        products = data_rows[data_rows['Items sold'] != 'AMAZON SUBSCRIPTION FEE']
        total_cost += products['Cost price'].sum()
        total_shipping += products['Shipping cost'].sum()
        if any(data_rows['Items sold'] == 'AMAZON SUBSCRIPTION FEE'):
            total_cost += 30

# Add unchanged sheets
for sheet in monthly_sales:
    if sheet not in updated_sheets:
        updated_sheets[sheet] = monthly_sales[sheet]

print(f"\nTotal cost: £{total_cost:.2f}")
print(f"Total shipping: £{total_shipping:.2f}")

# Save
with pd.ExcelWriter('data/reports/Amazon_Monthly_Sales_Corrected.xlsx', engine='xlsxwriter') as writer:
    for sheet, df in updated_sheets.items():
        df.to_excel(writer, sheet_name=sheet, index=False)

print("\nFile saved as 'Amazon_Monthly_Sales_Corrected.xlsx'")