# order_aggregator.py
"""
Aggregate monthly sales data to create consolidated CMS orders
Groups all sales by product for easy ordering
"""

import pandas as pd
import numpy as np
from datetime import datetime

class OrderAggregator:
    def __init__(self, monthly_data: dict):
        """
        Initialize with monthly data from MonthlySalesProcessor
        monthly_data: dict of {month_name: DataFrame}
        """
        self.monthly_data = monthly_data
        
    def create_aggregate_order(self) -> pd.DataFrame:
        """Create aggregated order summary across all months"""
        all_sales = []
        
        for month, df in self.monthly_data.items():
            # Determine which column to use for filtering
            if 'Sales record number' in df.columns:
                # eBay format
                id_col = 'Sales record number'
            elif 'Transaction ID' in df.columns:
                # Amazon format
                id_col = 'Transaction ID'
            else:
                continue
                
            # Skip total rows and fee rows
            sales_only = df[
                (df[id_col] != 'Total') & 
                (df[id_col] != '') &
                (df['Items sold'] != 'EBAY FEES FOR BUSINESS') &
                (df['Items sold'] != 'AMAZON SUBSCRIPTION FEE')
            ].copy()
            
            # Add month column for reference
            sales_only['Month'] = month
            all_sales.append(sales_only)
        
        # Combine all sales
        combined_df = pd.concat(all_sales, ignore_index=True)
        
        # Group by CMS product
        aggregated = self._aggregate_by_product(combined_df)
        
        # Handle special cases
        aggregated = self._handle_special_products(aggregated)
        
        return aggregated
    
    def _aggregate_by_product(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate sales by CMS product"""
        # Group by CMS name and code
        grouped = df.groupby(['Items sold', 'CMS code']).agg({
            'Quantity': 'sum',
            'Sold for': 'sum',
            'Cost price': 'sum',
            'NET PROFIT': 'sum',
            'Month': lambda x: ', '.join(sorted(set(x)))  # List months where sold
        }).reset_index()
        
        # Add average cost per unit for reference
        grouped['Unit cost'] = grouped['Cost price'] / grouped['Quantity']
        
        # Sort by quantity descending
        grouped = grouped.sort_values('Quantity', ascending=False)
        
        return grouped
    
    def _handle_special_products(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle special cases like Assorted Cosmetics"""
        # Separate regular products and special handling
        regular = df[~df['Items sold'].str.contains('ASSORTED_COSMETICS|MANUAL_ENTRY', na=False)]
        special = df[df['Items sold'].str.contains('ASSORTED_COSMETICS|MANUAL_ENTRY', na=False)]
        
        # Process Assorted Cosmetics
        if not special.empty:
            assorted = special[special['Items sold'] == 'Assorted Cosmetics']
            if not assorted.empty:
                # Sum all Flawlessly U products
                assorted_total = pd.DataFrame([{
                    'Items sold': 'Assorted Cosmetics (Flawlessly U)',
                    'CMS code': 'ASSORTED',
                    'Quantity': assorted['Quantity'].sum(),
                    'Sold for': assorted['Sold for'].sum(),
                    'Cost price': assorted['Cost price'].sum(),
                    'NET PROFIT': assorted['NET PROFIT'].sum(),
                    'Month': 'Multiple',
                    'Unit cost': assorted['Cost price'].sum() / assorted['Quantity'].sum(),
                    'CMS_note': f'Total value: £{assorted["Cost price"].sum():.2f}'
                }])
                
                regular = pd.concat([regular, assorted_total], ignore_index=True)
        
        return regular
    
    def create_cms_order_list(self, aggregated_df: pd.DataFrame) -> pd.DataFrame:
        """
        Create final order list formatted for CMS ordering
        Includes product codes and consolidated quantities
        """
        # Filter out items without CMS codes or unmatched items
        cms_ready = aggregated_df[
            (aggregated_df['CMS code'] != 'NO_CODE') & 
            (aggregated_df['CMS code'] != 'NO_MATCH') &
            (aggregated_df['CMS code'].notna())
        ].copy()
        
        # Create order format
        order_list = cms_ready[['CMS code', 'Items sold', 'Quantity', 'Unit cost', 'Cost price']].copy()
        
        # Round quantities up for ordering (can't order partial units)
        order_list['Order Quantity'] = np.ceil(order_list['Quantity']).astype(int)
        
        # Add order value
        order_list['Order Value'] = order_list['Order Quantity'] * order_list['Unit cost']
        
        # Add notes for special handling
        order_list['Notes'] = ''
        
        # Flag high-value items
        order_list.loc[order_list['Order Value'] > 50, 'Notes'] = 'High value - verify before ordering'
        
        # Sort by order value descending
        order_list = order_list.sort_values('Order Value', ascending=False)
        
        # Add totals row
        totals = pd.DataFrame([{
            'CMS code': 'TOTAL',
            'Items sold': '',
            'Quantity': order_list['Quantity'].sum(),
            'Order Quantity': order_list['Order Quantity'].sum(),
            'Unit cost': '',
            'Cost price': order_list['Cost price'].sum(),
            'Order Value': order_list['Order Value'].sum(),
            'Notes': f'Total items: {len(order_list)}'
        }])
        
        order_list = pd.concat([order_list, totals], ignore_index=True)
        
        return order_list
    
    def export_order_summary(self, aggregated_df: pd.DataFrame, order_list_df: pd.DataFrame, 
                           output_file: str = 'data/reports/CMS_Order_Summary.xlsx'):
        """Export order summary to Excel with multiple sheets"""
        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
            # Sheet 1: Detailed aggregation
            aggregated_df.to_excel(writer, sheet_name='Aggregate_Sales', index=False)
            
            # Sheet 2: CMS order list
            order_list_df.to_excel(writer, sheet_name='CMS_Order_List', index=False)
            
            # Sheet 3: Products needing manual review
            unmatched = aggregated_df[
                (aggregated_df['CMS code'] == 'NO_CODE') | 
                (aggregated_df['CMS code'] == 'NO_MATCH') |
                (aggregated_df['Items sold'].str.contains('UNMATCHED:', na=False))
            ]
            if not unmatched.empty:
                unmatched.to_excel(writer, sheet_name='Needs_Review', index=False)
            
            # Format sheets
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                workbook = writer.book
                
                # Add formats
                try:
                    money_format = workbook.add_format({'num_format': '£#,##0.00'})
                    header_format = workbook.add_format({
                        'bold': True,
                        'bg_color': '#D9E1F2',
                        'border': 1
                    })
                    
                    # Apply formatting based on sheet
                    if sheet_name == 'CMS_Order_List':
                        # Highlight totals row
                        total_format = workbook.add_format({
                            'bold': True,
                            'bg_color': '#FFE699',
                            'border': 1
                        })
                        last_row = len(order_list_df) - 1
                        for col in range(len(order_list_df.columns)):
                            worksheet.write(last_row + 1, col, 
                                          order_list_df.iloc[last_row, col], 
                                          total_format)
                except:
                    pass
        
        print(f"Order summary exported to {output_file}")
        return output_file


# Usage example
if __name__ == "__main__":
    from monthly_sales_processor import MonthlySalesProcessor
    from product_catalogue_manager import ProductCatalogueManager
    
    # Assuming you have monthly_data from the processor
    catalogue = ProductCatalogueManager()
    processor = MonthlySalesProcessor(catalogue)
    monthly_data = processor.process_sales_data('data/input/eBay-OrdersReport-Aug-13-2025-14%3A49%3A20-0700-13243478577.csv')
    
    # Create aggregator
    aggregator = OrderAggregator(monthly_data)
    
    # Generate aggregate order
    aggregated = aggregator.create_aggregate_order()
    print(f"\nTotal unique products to order: {len(aggregated)}")
    
    # Create CMS order list
    order_list = aggregator.create_cms_order_list(aggregated)
    print(f"CMS-ready products: {len(order_list) - 1}")  # Minus total row
    
    # Export
    aggregator.export_order_summary(aggregated, order_list)
    
    # Print summary
    total_value = order_list[order_list['CMS code'] == 'TOTAL']['Order Value'].values[0]
    print(f"\nTotal order value: £{total_value:.2f}")