# create_combined_cms_order.py

from src.product_catalogue_manager import ProductCatalogueManager
from src.monthly_sales_processor import MonthlySalesProcessor
from src.amazon_sales_processor import AmazonSalesProcessor
from src.order_aggregator import OrderAggregator

# Initialize
print("Initializing catalogue...")
catalogue = ProductCatalogueManager()

# Process eBay sales
print("\nProcessing eBay sales...")
ebay_processor = MonthlySalesProcessor(catalogue)
ebay_monthly = ebay_processor.process_sales_data('data/input/eBayOrdersReportAug132025143A493A20070013243478577.csv')
ebay_processor.export_to_excel(ebay_monthly, 'data/reports/eBay_Monthly_Sales.xlsx')

# Process Amazon sales
print("\nProcessing Amazon sales...")
amazon_processor = AmazonSalesProcessor(catalogue)
amazon_monthly = amazon_processor.process_sales_data('data/input/Amazon_Sales_2024Sep-2025Sep.csv')
amazon_processor.export_to_excel(amazon_monthly, 'data/reports/Amazon_Monthly_Sales.xlsx')

# Combine all monthly data from both channels
print("\nCombining data from both channels...")
all_monthly_data = {**ebay_monthly, **amazon_monthly}

# Create aggregate order
print("\nCreating consolidated CMS order...")
aggregator = OrderAggregator(all_monthly_data)
aggregated = aggregator.create_aggregate_order()
order_list = aggregator.create_cms_order_list(aggregated)

# Export combined order
aggregator.export_order_summary(aggregated, order_list, 'data/reports/Combined_CMS_Order.xlsx')

# Print summary
total_products = len(order_list) - 1  # Minus the total row
total_value = order_list[order_list['CMS code'] == 'TOTAL']['Order Value'].values[0]

print("\n" + "="*50)
print("COMBINED CMS ORDER SUMMARY")
print("="*50)
print(f"Total unique products to order: {total_products}")
print(f"Total order value: £{total_value:,.2f}")
print("\nOrder saved to: data/reports/Combined_CMS_Order.xlsx")
print("\nThe CMS_Order_List sheet contains your consolidated order!")