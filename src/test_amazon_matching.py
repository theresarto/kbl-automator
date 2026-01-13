# Create a test script to generate Amazon matching report
# save as: test_amazon_matching.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.product_catalogue_manager import ProductCatalogueManager
from src.amazon_sales_processor import AmazonSalesProcessor

import pandas as pd

# Initialize
catalogue = ProductCatalogueManager()
processor = AmazonSalesProcessor(catalogue)

# Parse Amazon data
amazon_df = processor.parse_amazon_csv('data/input/Amazon_Sales_2024Sep-2025Sep.csv')

# Get unique products
unique_products = amazon_df['description'].unique()
print(f"\nFound {len(unique_products)} unique products in Amazon data\n")

# Test matching for each product
results = []
for product in unique_products:
    if pd.notna(product):
        # Parse bundles
        bundle_qty, clean_title = processor.parse_bundle_quantity(product)
        
        # Try matching
        matches = catalogue.match_ebay_title(clean_title)
        
        result = {
            'amazon_title': product,
            'clean_title': clean_title,
            'bundle_qty': bundle_qty,
            'matched': 'YES' if matches else 'NO',
            'best_match': matches[0]['cms_name'] if matches else '',
            'confidence': f"{matches[0]['confidence']:.1%}" if matches else '0%',
            'cms_code': matches[0]['cms_code'] if matches else ''
        }
        results.append(result)

# Create report
report_df = pd.DataFrame(results)

# Save to Excel with separate sheets
with pd.ExcelWriter('data/reports/Amazon_Matching_Report.xlsx', engine='xlsxwriter') as writer:
    # All products
    report_df.to_excel(writer, sheet_name='All_Products', index=False)
    
    # Unmatched only
    unmatched = report_df[report_df['matched'] == 'NO']
    unmatched.to_excel(writer, sheet_name='Unmatched_Products', index=False)
    
    # Summary stats
    summary = pd.DataFrame([
        {'Metric': 'Total Products', 'Count': len(report_df)},
        {'Metric': 'Matched', 'Count': len(report_df[report_df['matched'] == 'YES'])},
        {'Metric': 'Unmatched', 'Count': len(report_df[report_df['matched'] == 'NO'])},
        {'Metric': 'Match Rate', 'Count': f"{len(report_df[report_df['matched'] == 'YES']) / len(report_df) * 100:.1f}%"}
    ])
    summary.to_excel(writer, sheet_name='Summary', index=False)

print("Matching report saved to: data/reports/Amazon_Matching_Report.xlsx")
print(f"\nUnmatched products ({len(unmatched)}):")
for _, row in unmatched.iterrows():
    print(f"- {row['amazon_title']}")

# Check specifically for Cream Silk
cream_silk_products = report_df[report_df['amazon_title'].str.contains('Cream Silk', case=False, na=False)]
print(f"\nCream Silk products found: {len(cream_silk_products)}")
for _, row in cream_silk_products.iterrows():
    print(f"- {row['amazon_title']} -> Matched: {row['matched']}")
    