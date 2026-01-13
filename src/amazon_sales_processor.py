# amazon_sales_processor.py
"""
Process Amazon sales data into monthly accounting sheets
Handles bundles, fees, VAT, and subscription costs
"""

import pandas as pd
import numpy as np
from datetime import datetime
import re
import os
from product_catalogue_manager import ProductCatalogueManager

class AmazonSalesProcessor:
    def __init__(self, catalogue_manager: ProductCatalogueManager):
        self.catalogue = catalogue_manager
        self.vat_rate = 0.20
        self.amazon_monthly_fee = 30.00  # £30 subscription inc VAT
        
    def parse_bundle_quantity(self, item_title: str) -> tuple:
        """
        Extract quantity from Amazon bundle descriptions
        Returns: (quantity, cleaned_title)
        """
        if pd.isna(item_title):
            return 1, ""
            
        item_title = str(item_title)
        
        # Pattern for "X Pack of" or "Pack of X"
        pack_match = re.search(r'(\d+)\s*Pack\s+of\s+', item_title, re.IGNORECASE)
        if pack_match:
            quantity = int(pack_match.group(1))
            clean_title = re.sub(r'\d+\s*Pack\s+of\s+', '', item_title, flags=re.IGNORECASE).strip()
            return quantity, clean_title
        
        # Pattern for "Lot of X"
        lot_match = re.search(r'Lot\s+of\s+(\d+)\s+', item_title, re.IGNORECASE)
        if lot_match:
            quantity = int(lot_match.group(1))
            clean_title = re.sub(r'Lot\s+of\s+\d+\s+', '', item_title, flags=re.IGNORECASE).strip()
            return quantity, clean_title
        
        # Pattern for "Bundle of X"
        bundle_match = re.search(r'Bundle\s+of\s+(\d+)', item_title, re.IGNORECASE)
        if bundle_match:
            quantity = int(bundle_match.group(1))
            clean_title = re.sub(r'Bundle\s+of\s+\d+\s*', '', item_title, flags=re.IGNORECASE).strip()
            return quantity, clean_title
        
        return 1, item_title
    
    # Update the parse_amazon_csv method in amazon_sales_processor.py:
    def parse_amazon_csv(self, filepath: str) -> pd.DataFrame:
        """Parse Amazon CSV and extract sales data"""
        # Read CSV skipping the header description rows
        df = pd.read_csv(filepath, skiprows=7, encoding='utf-8')
        
        print(f"Loaded {len(df)} rows from Amazon CSV")
        print(f"Columns found: {list(df.columns)[:5]}...")
        
        # The date column is 'date/time' based on the header
        date_col = 'date/time'
        
        # Parse dates - Amazon uses UTC
        df[date_col] = pd.to_datetime(df[date_col], utc=True)
        
        # Filter to tax year (April 2024 - March 2025) - make timestamps timezone-aware
        start_date = pd.Timestamp('2024-04-01', tz='UTC')
        end_date = pd.Timestamp('2025-03-31', tz='UTC')
        
        df = df[(df[date_col] >= start_date) & (df[date_col] <= end_date)].copy()
        
        # Convert to local time if needed (optional)
        # df[date_col] = df[date_col].dt.tz_convert('Europe/London')
        
        # Add month column
        df['Sale month'] = df[date_col].dt.strftime('%B %Y')
        
        # Filter out subscription fees
        sales_df = df[~((df['type'] == 'Service Fee') & (df['description'] == 'Subscription'))].copy()
        
        # Also filter out the Debt entries
        sales_df = sales_df[sales_df['type'] != 'Debt'].copy()
        
        # Filter to only actual sales
        sales_df = sales_df[sales_df['order id'].notna() & (sales_df['order id'] != '')].copy()
        
        print(f"Found {len(sales_df)} sales transactions after filtering")
        
        return sales_df
    
    def calculate_amazon_fees(self, sale_amount: float) -> dict:
        """
        Calculate Amazon selling fees
        Amazon typically charges ~15% referral fee + fulfillment fees
        """
        # Simplified fee structure - adjust based on your actual fees
        referral_fee_rate = 0.15  # 15% referral fee
        
        referral_fee = sale_amount * referral_fee_rate
        
        # Add VAT
        total_fee_exc_vat = referral_fee
        total_fee_inc_vat = total_fee_exc_vat * 1.2
        
        return {
            'referral_fee': referral_fee,
            'total_fee': total_fee_inc_vat,
            'total_exc_vat': total_fee_exc_vat
        }
    
    def process_sales_data(self, amazon_csv_path: str) -> dict:
        """Process Amazon sales data and create monthly summaries"""
        # Parse Amazon data
        sales_df = self.parse_amazon_csv(amazon_csv_path)
        
        print(f"Processing Amazon sales from {sales_df['Sale month'].min()} to {sales_df['Sale month'].max()}")
        
        matched_data = []
        
        # For Amazon, the item details are usually in 'description' column
        item_col = 'description'  # Changed from searching for 'item title'
        quantity_col = 'quantity'
        amount_col = 'total'  # The total column from Amazon
        
        print(f"Using columns: item='{item_col}', quantity='{quantity_col}', amount='{amount_col}'")
        
        for idx, row in sales_df.iterrows():
            item_title = row.get(item_col, '')
            
            # Skip if no item title
            if pd.isna(item_title) or item_title == '':
                continue
            
            # Parse bundle quantity
            bundle_qty, clean_title = self.parse_bundle_quantity(item_title)
            
            # Get quantity from order
            order_qty = row.get(quantity_col, 1) if quantity_col else 1
            if pd.isna(order_qty):
                order_qty = 1
            
            # Total quantity = bundle quantity × order quantity
            total_qty = bundle_qty * order_qty
            
            # Match product
            matches = self.catalogue.match_ebay_title(clean_title)  # Same matching logic
            
            if matches:
                match = matches[0]
                matched_row = self._create_matched_row(row, match, total_qty, item_col, amount_col)
                matched_data.append(matched_row)
            else:
                print(f"Warning: No match for {clean_title}")
                unmatched_row = self._create_unmatched_row(row, total_qty, item_col, amount_col)
                matched_data.append(unmatched_row)
        
        # Create DataFrame
        processed_df = pd.DataFrame(matched_data)
        
        # Group by month
        monthly_data = {}
        for month in processed_df['Sale month'].unique():
            month_df = processed_df[processed_df['Sale month'] == month].copy()
            monthly_data[month] = self._create_monthly_summary(month_df)
        
        return monthly_data
    
    def _create_matched_row(self, amazon_row: pd.Series, match: dict, quantity: int, 
                        item_col: str, amount_col: str) -> dict:
        """Create a row with matched product data"""
        # Get sale amount
        sale_amount = amazon_row.get(amount_col, 0)
        if pd.isna(sale_amount):
            sale_amount = 0
        else:
            sale_amount = float(str(sale_amount).replace('£', '').replace(',', ''))
        
        # Calculate fees
        fees = self.calculate_amazon_fees(sale_amount)
        
        # Fixed shipping cost
        shipping_cost = 3.21  # Fixed rate before March 19, 2025
        
        # Calculate costs
        cost_price = match['wholesale_price'] * quantity
        cost_exc_vat = cost_price / 1.2
        
        # Net profit = Sale amount - Amazon fees - Shipping cost - Product cost
        net_profit = sale_amount - fees['total_fee'] - shipping_cost - cost_price
        
        # Get sale date and remove timezone
        sale_date = amazon_row.get('date/time', '')
        if hasattr(sale_date, 'tz_localize'):
            sale_date = sale_date.tz_localize(None)
        
        return {
            'Transaction ID': amazon_row.get('Transaction ID', ''),
            'Sale date': sale_date,
            'Sale month': amazon_row['Sale month'],
            'Items sold': match['cms_name'],
            'Amazon title': amazon_row[item_col],
            'CMS code': match.get('cms_code', ''),
            'Quantity': quantity,
            'Sold for': sale_amount,
            'Shipping cost': shipping_cost,  # Add this column
            'Amazon fees': fees['total_fee'],
            'Cost price': cost_price,
            'COST LESS VAT': cost_exc_vat,
            'NET PROFIT': net_profit,
            'Match confidence': match.get('confidence', 1.0)
        }
    
    def _create_unmatched_row(self, amazon_row: pd.Series, quantity: int, 
                            item_col: str, amount_col: str) -> dict:
        """Create a row for unmatched products"""
        sale_amount = amazon_row.get(amount_col, 0)
        if pd.isna(sale_amount):
            sale_amount = 0
        else:
            sale_amount = float(str(sale_amount).replace('£', '').replace(',', ''))
        
        fees = self.calculate_amazon_fees(sale_amount)
        
        return {
            'Transaction ID': amazon_row.get('Transaction ID', ''),
            'Sale date': amazon_row.get('Date', amazon_row.get('date/time', '')),
            'Sale month': amazon_row['Sale month'],
            'Items sold': f"UNMATCHED: {amazon_row[item_col]}",
            'Amazon title': amazon_row[item_col],
            'CMS code': 'NO_MATCH',
            'Quantity': quantity,
            'Sold for': sale_amount,
            'Amazon fees': fees['total_fee'],
            'Cost price': 0,
            'COST LESS VAT': 0,
            'NET PROFIT': sale_amount - fees['total_fee'],
            'Match confidence': 0
        }
    
    def _create_monthly_summary(self, month_df: pd.DataFrame) -> pd.DataFrame:
        """Create summary for a specific month"""
        # Add monthly subscription fee
        monthly_fees = pd.DataFrame([{
            'Transaction ID': '',
            'Sale date': '',
            'Items sold': 'AMAZON SUBSCRIPTION FEE',
            'Quantity': '',
            'Sold for': '',
            'Amazon fees': self.amazon_monthly_fee,
            'Cost price': 0,
            'COST LESS VAT': 0,
            'NET PROFIT': -self.amazon_monthly_fee
        }])
        
        # Combine with sales data
        summary_df = pd.concat([monthly_fees, month_df], ignore_index=True)
        
        # Add totals row
        totals = {
            'Transaction ID': 'Total',
            'Items sold': '',
            'Quantity': month_df['Quantity'].sum() if not month_df.empty else 0,
            'Sold for': month_df['Sold for'].sum() if not month_df.empty else 0,
            'Amazon fees': (month_df['Amazon fees'].sum() if not month_df.empty else 0) + self.amazon_monthly_fee,
            'Cost price': month_df['Cost price'].sum() if not month_df.empty else 0,
            'COST LESS VAT': month_df['COST LESS VAT'].sum() if not month_df.empty else 0,
            'NET PROFIT': (month_df['NET PROFIT'].sum() if not month_df.empty else 0) - self.amazon_monthly_fee
        }
        
        summary_df = pd.concat([summary_df, pd.DataFrame([totals])], ignore_index=True)
        
        return summary_df
    
    def export_to_excel(self, monthly_data: dict, output_file: str):
        """Export monthly data to Excel with formatting"""
        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
            for month, df in monthly_data.items():
                # Clean month name for sheet name
                sheet_name = month.upper().replace(' ', '_')
                
                # Remove timezone from ALL datetime columns before export
                df_copy = df.copy()
                
                # Check each column and convert datetime columns
                for col in df_copy.columns:
                    if col in ['Sale date', 'date/time'] or 'date' in col.lower():
                        try:
                            # Convert to datetime if it's not already
                            df_copy[col] = pd.to_datetime(df_copy[col], errors='coerce')
                            # Remove timezone if present
                            if hasattr(df_copy[col], 'dt'):
                                if df_copy[col].dt.tz is not None:
                                    df_copy[col] = df_copy[col].dt.tz_localize(None)
                        except:
                            pass
                
                # Write data
                df_copy.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Get workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets[sheet_name]
                
                # Format columns
                try:
                    money_format = workbook.add_format({'num_format': '£#,##0.00'})
                    
                    # Apply money format
                    money_columns = ['Sold for', 'Amazon fees', 'Cost price', 'COST LESS VAT', 'NET PROFIT']
                    for col_name in money_columns:
                        if col_name in df.columns:
                            col_idx = df.columns.get_loc(col_name)
                            worksheet.set_column(col_idx, col_idx, 15, money_format)
                except:
                    pass
        
        print(f"Amazon monthly sales data exported to {output_file}")


# Example usage
if __name__ == "__main__":
    from product_catalogue_manager import ProductCatalogueManager
    
    # Initialize
    catalogue = ProductCatalogueManager()
    processor = AmazonSalesProcessor(catalogue)
    
    # Process Amazon sales
    monthly_data = processor.process_sales_data('data/input/Amazon_Sales_2024Sep-2025Sep.csv')
    
    # Export to Excel
    processor.export_to_excel(monthly_data, 'data/reports/Amazon_Monthly_Sales.xlsx')
    
    # Print summary
    for month, df in monthly_data.items():
        print(f"\n{month} Amazon Summary:")
        sales_only = df[df['Transaction ID'] != 'Total']
        if not sales_only.empty:
            total_sales = pd.to_numeric(sales_only['Sold for'], errors='coerce').sum()
            print(f"Total sales: £{total_sales:.2f}")
        
        total_row = df[df['Transaction ID'] == 'Total']
        if not total_row.empty:
            net_profit = total_row['NET PROFIT'].iloc[0]
            print(f"Total profit: £{net_profit:.2f}")