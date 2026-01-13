# create_combined_cms_order_same_period.py


import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.product_catalogue_manager import ProductCatalogueManager
from src.monthly_sales_processor import MonthlySalesProcessor
from src.amazon_sales_processor import AmazonSalesProcessor
from src.order_aggregator import OrderAggregator

# Initialize
catalogue = ProductCatalogueManager()

# Process both channels
print("Processing eBay sales...")
ebay_processor = MonthlySalesProcessor(catalogue)
ebay_monthly = ebay_processor.process_sales_data('data/input/eBay-OrdersReport-Aug-13-2025-14%3A49%3A20-0700-13243478577.csv')

print("Processing Amazon sales...")
amazon_processor = AmazonSalesProcessor(catalogue)
amazon_monthly = amazon_processor.process_sales_data('data/input/Amazon_Sales_2024Sep-2025Sep.csv')

# Find overlapping months
ebay_months = set(ebay_monthly.keys())
amazon_months = set(amazon_monthly.keys())
common_months = ebay_months.intersection(amazon_months)

print(f"\neBay months: {sorted(ebay_months)}")
print(f"Amazon months: {sorted(amazon_months)}")
print(f"Overlapping months: {sorted(common_months)}")

# Filter to only overlapping months
filtered_monthly_data = {}
for month in common_months:
    # Combine same months from both channels
    filtered_monthly_data[f"{month}_eBay"] = ebay_monthly[month]
    filtered_monthly_data[f"{month}_Amazon"] = amazon_monthly[month]

print(f"\nCreating order for overlapping period only: {sorted(common_months)}")

# Create aggregate order
aggregator = OrderAggregator(filtered_monthly_data)
aggregated = aggregator.create_aggregate_order()
order_list = aggregator.create_cms_order_list(aggregated)

# Export
aggregator.export_order_summary(aggregated, order_list, 'data/reports/Combined_CMS_Order_Same_Period.xlsx')