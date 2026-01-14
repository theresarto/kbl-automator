# create_amazon_order_nov2024_mar2025.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.product_catalogue_manager import ProductCatalogueManager
from src.amazon_sales_processor import AmazonSalesProcessor
from src.order_aggregator import OrderAggregator

# Initialize
catalogue = ProductCatalogueManager()

# Process only Amazon sales for the period you need
print("Processing Amazon sales (Nov 2024 - Mar 2025)...")
amazon_processor = AmazonSalesProcessor(catalogue)
amazon_monthly = amazon_processor.process_sales_data('data/input/Amazon_Sales_2024Sep-2025Sep.csv')

# Filter to only Nov 2024 - Mar 2025
filtered_months = ['November 2024', 'December 2024', 'January 2025', 'February 2025', 'March 2025']
filtered_data = {month: amazon_monthly[month] for month in filtered_months if month in amazon_monthly}

print(f"\nProcessing months: {list(filtered_data.keys())}")

# ADD THE DEBUG CODE HERE:
# Check data types
for month, df in filtered_data.items():
    print(f"\n{month} data types:")
    print(df[['Quantity', 'Sold for', 'Cost price']].dtypes)


# Create aggregate order
aggregator = OrderAggregator(filtered_data)

# Debug the aggregation process
print("\nDEBUG - Before aggregation:")
for month, df in filtered_data.items():
    sales_only = df[
        (df['Transaction ID'] != 'Total') & 
        (df['Transaction ID'] != '') &
        (df['Items sold'] != 'AMAZON SUBSCRIPTION FEE')
    ]
    print(f"{month}: {len(sales_only)} sales rows")

aggregated = aggregator.create_aggregate_order()
print(f"\nDEBUG - After aggregation: {len(aggregated)} rows")
print(aggregated.head() if len(aggregated) > 0 else "EMPTY DATAFRAME")

order_list = aggregator.create_cms_order_list(aggregated)
print(f"\nDEBUG - CMS order list: {len(order_list)} rows")

# Export
aggregator.export_order_summary(aggregated, order_list, 'data/reports/Amazon_CMS_Order_Nov2024_Mar2025.xlsx')

print("\nAmazon order for Nov 2024 - Mar 2025 created!")
print("Check: data/reports/Amazon_CMS_Order_Nov2024_Mar2025.xlsx")