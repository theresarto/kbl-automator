# monthly_sales_processor.py
"""
Process eBay sales data into monthly accounting sheets
Handles fees, VAT, promoted listings, and special cases
"""

import pandas as pd
import numpy as np
from datetime import datetime
import re
import os
from product_catalogue_manager import ProductCatalogueManager

class MonthlySalesProcessor:
    def __init__(self, catalogue_manager: ProductCatalogueManager):
        self.catalogue = catalogue_manager
        self.vat_rate = 0.20
        self.ebay_monthly_fee = 32.40  # Inc VAT
        self.shopify_monthly_fee = 25.00  # Inc VAT
        
    def calculate_ebay_fees(self, sold_for: float, is_promoted: bool = False) -> dict:
        """
        Calculate eBay fees including VAT
        Returns dict with breakdown of fees
        """
        # Base fee calculation
        base_fee_calc = (
            (sold_for * 0.109) + 
            (sold_for * 0.0035) - 
            (sold_for * 0.109 * 0.1) + 
            0.3
        ) * 1.2  # VAT included
        
        # Promoted listing fee if applicable
        promoted_fee = 0
        if is_promoted:
            promoted_fee = 0.02 * sold_for * 1.2  # 2% + VAT
        
        total_fee = base_fee_calc + promoted_fee
        
        return {
            'base_fee': base_fee_calc,
            'promoted_fee': promoted_fee,
            'total_fee': total_fee,
            'total_exc_vat': total_fee / 1.2
        }
    
    def parse_ebay_csv(self, filepath: str) -> pd.DataFrame:
        """Parse eBay CSV and extract sales data"""
        # Read CSV and find header
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        header_idx = next(i for i, line in enumerate(lines) if 'Sales record number' in line)
        
        # Read data
        df = pd.read_csv(filepath, skiprows=header_idx)
        
        # Filter to only rows with item titles (child rows)
        sales_df = df[df['Item title'].notna()].copy()
        
        # Parse sale date
        sales_df['Sale date'] = pd.to_datetime(sales_df['Sale date'])
        sales_df['Sale month'] = sales_df['Sale date'].dt.strftime('%B %Y')
        
        # Clean up sold for price
        sales_df['Sold for'] = sales_df['Sold for'].str.replace('£', '').astype(float)
        
        # Check promoted listing
        sales_df['Is promoted'] = sales_df['Sold via Promoted listings'] == 'Yes'
        
        return sales_df
    
    def process_sales_data(self, ebay_csv_path: str) -> dict:
        """
        Process eBay sales data and create monthly summaries
        Returns dict of DataFrames by month
        """
        # Parse eBay data
        sales_df = self.parse_ebay_csv(ebay_csv_path)
        
        # Add product matching
        print("Matching products to CMS catalogue...")
        matched_data = []
        
        for idx, row in sales_df.iterrows():
            # Match product
            matches = self.catalogue.match_ebay_title(row['Item title'])
            
            if matches:
                # Handle product sets
                if len(matches) > 1 and all(m.get('special_handling') == 'product_set' for m in matches):
                    # Split quantity among set items
                    qty_per_item = row['Quantity'] / len(matches)
                    for match in matches:
                        matched_row = self._create_matched_row(row, match, qty_per_item)
                        matched_data.append(matched_row)
                else:
                    # Single product or best match
                    match = matches[0]
                    
                    # Check for bundle multiplier
                    if match.get('special_handling') == 'bundle_multiply':
                        quantity = row['Quantity'] * match.get('bundle_quantity', 1)
                    else:
                        quantity = row['Quantity']
                    
                    matched_row = self._create_matched_row(row, match, quantity)
                    matched_data.append(matched_row)
            else:
                # No match found
                print(f"Warning: No match for {row['Item title']}")
                matched_row = self._create_unmatched_row(row)
                matched_data.append(matched_row)
        
        # Create DataFrame
        processed_df = pd.DataFrame(matched_data)
        
        # Group by month
        monthly_data = {}
        for month in processed_df['Sale month'].unique():
            month_df = processed_df[processed_df['Sale month'] == month].copy()
            monthly_data[month] = self._create_monthly_summary(month_df)
        
        return monthly_data
    
    def _create_matched_row(self, ebay_row: pd.Series, match: dict, quantity: float) -> dict:
        """Create a row with matched product data"""
        # Calculate fees
        fees = self.calculate_ebay_fees(ebay_row['Sold for'], ebay_row['Is promoted'])
        
        # Get postage cost based on delivery service
        postage_cost = self._get_postage_cost(ebay_row)
        
        # Calculate costs and profit
        cost_price = match['wholesale_price'] * quantity
        cost_exc_vat = cost_price / 1.2
        
        # Net profit = Sale price - All costs (inc VAT)
        net_profit = ebay_row['Sold for'] - fees['total_fee'] - postage_cost - cost_price
        
        return {
            'Sales record number': ebay_row['Sales record number'],
            'Order number': ebay_row['Order number'],
            'Sale date': ebay_row['Sale date'],
            'Sale month': ebay_row['Sale month'],
            'Items sold': match['cms_name'],
            'eBay title': ebay_row['Item title'],
            'CMS code': match.get('cms_code', ''),
            'Quantity': quantity,
            'Sold for': ebay_row['Sold for'],
            'Postage': postage_cost,
            'Promoted listing': 'Yes' if ebay_row['Is promoted'] else 'No',
            'EBAY FEES': fees['total_fee'],
            'Cost price': cost_price,
            'COST LESS VAT': cost_exc_vat,
            'NET PROFIT': net_profit,
            'Delivery service': ebay_row.get('Delivery service', ''),
            'Tracking number': ebay_row.get('Tracking number', ''),
            'Match confidence': match.get('confidence', 1.0),
            'Special handling': match.get('special_handling', '')
        }
    
    def _create_unmatched_row(self, ebay_row: pd.Series) -> dict:
        """Create a row for unmatched products"""
        fees = self.calculate_ebay_fees(ebay_row['Sold for'], ebay_row['Is promoted'])
        postage_cost = self._get_postage_cost(ebay_row)
        
        return {
            'Sales record number': ebay_row['Sales record number'],
            'Order number': ebay_row['Order number'],
            'Sale date': ebay_row['Sale date'],
            'Sale month': ebay_row['Sale month'],
            'Items sold': f"UNMATCHED: {ebay_row['Item title']}",
            'eBay title': ebay_row['Item title'],
            'CMS code': 'NO_MATCH',
            'Quantity': ebay_row['Quantity'],
            'Sold for': ebay_row['Sold for'],
            'Postage': postage_cost,
            'Promoted listing': 'Yes' if ebay_row['Is promoted'] else 'No',
            'EBAY FEES': fees['total_fee'],
            'Cost price': 0,
            'COST LESS VAT': 0,
            'NET PROFIT': ebay_row['Sold for'] - fees['total_fee'] - postage_cost,
            'Delivery service': ebay_row.get('Delivery service', ''),
            'Tracking number': ebay_row.get('Tracking number', ''),
            'Match confidence': 0,
            'Special handling': 'needs_manual_review'
        }
    
    def _get_postage_cost(self, row: pd.Series) -> float:
        """Get postage cost based on delivery service and tracking"""
        delivery = str(row.get('Delivery service', '')).lower()
        tracking = str(row.get('Tracking number', ''))
        
        # Check delivery service
        if 'royal mail tracked 48' in delivery:
            if tracking.startswith('QM'):
                # Tracked 48 Letter
                base = 1.90 + 0.04  # Base + green surcharge
                with_surcharge = base * 1.08  # 8% fuel surcharge
                return with_surcharge * 1.2  # Add VAT
            else:
                # Standard Tracked 48
                base = 2.60 + 0.04
                with_surcharge = base * 1.08
                return with_surcharge * 1.2
        
        elif 'royal mail tracked 24' in delivery:
            base = 3.20 + 0.04
            with_surcharge = base * 1.08
            return with_surcharge * 1.2
        
        elif tracking and tracking[0].isdigit():
            # DPD (starts with digit)
            return 5.32 * 1.2  # £5.32 + VAT
        
        # Default
        return 3.42  # Standard rate inc VAT
    
    def _create_monthly_summary(self, month_df: pd.DataFrame) -> pd.DataFrame:
        """Create summary for a specific month"""
        # Add monthly fees row
        monthly_fees = pd.DataFrame([{
            'Sales record number': '',
            'Order number': '',
            'Items sold': 'EBAY FEES FOR BUSINESS',
            'Quantity': '',
            'Sold for': '',
            'Postage': '',
            'EBAY FEES': self.ebay_monthly_fee,
            'Cost price': 0,
            'COST LESS VAT': 0,
            'NET PROFIT': -self.ebay_monthly_fee
        }])
        
        # Combine with sales data
        summary_df = pd.concat([monthly_fees, month_df], ignore_index=True)
        
        # Add totals row
        totals = {
            'Sales record number': 'Total',
            'Order number': '',
            'Items sold': '',
            'Quantity': month_df['Quantity'].sum(),
            'Sold for': month_df['Sold for'].sum(),
            'Postage': month_df['Postage'].sum(),
            'EBAY FEES': month_df['EBAY FEES'].sum() + self.ebay_monthly_fee,
            'Cost price': month_df['Cost price'].sum(),
            'COST LESS VAT': month_df['COST LESS VAT'].sum(),
            'NET PROFIT': month_df['NET PROFIT'].sum() - self.ebay_monthly_fee
        }
        
        summary_df = pd.concat([summary_df, pd.DataFrame([totals])], ignore_index=True)
        
        return summary_df
    
    def export_to_excel(self, monthly_data: dict, output_file: str):
        """Export monthly data to Excel with formatting"""
        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
            for month, df in monthly_data.items():
                # Clean month name for sheet name
                sheet_name = month.upper().replace(' ', '_')
                
                # Write data
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Get workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets[sheet_name]
                
                # Ensure workbook is an xlsxwriter Workbook
                try:
                    money_format = workbook.add_format({'num_format': '£#,##0.00'})
                    header_format = workbook.add_format({
                        'bold': True,
                        'bg_color': '#D9E1F2',
                        'border': 1
                    })
                except AttributeError:
                    # Fallback: skip formatting if not xlsxwriter
                    print("Warning: Excel formatting not available. Exporting without formatting.")
                    money_format = None
                    header_format = None
                
                # Apply formats
                for col_num, col_name in enumerate(df.columns):
                    if money_format and col_name in ['Sold for', 'Postage', 'EBAY FEES', 'Cost price', 'COST LESS VAT', 'NET PROFIT']:
                        worksheet.set_column(col_num, col_num, 12, money_format)
                    
                    # Write header with format
                    if header_format:
                        worksheet.write(0, col_num, col_name, header_format)
                
                # Autofit columns (if available)
                if hasattr(worksheet, 'autofit'):
                    worksheet.autofit()
        
        print(f"Monthly sales data exported to {output_file}")


# Example usage
if __name__ == "__main__":
    # Initialize catalogue manager
    catalogue = ProductCatalogueManager()
    
    # Initialize sales processor
    processor = MonthlySalesProcessor(catalogue)
    
    # Process sales data
    monthly_data = processor.process_sales_data('data/input/eBay-OrdersReport-Aug-13-2025-14%3A49%3A20-0700-13243478577.csv')
    
    # Export to Excel
    processor.export_to_excel(monthly_data, 'data/reports/Monthly_Sales_Summary.xlsx')
    
    # Print summary
    for month, df in monthly_data.items():
        print(f"\n{month} Summary:")
        print(f"Total sales: £{df[df['Sales record number'] != 'Total']['Sold for'].sum():.2f}")
        print(f"Total profit: £{df[df['Sales record number'] == 'Total']['NET PROFIT'].values[0]:.2f}")