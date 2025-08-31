"""
Product Catalogue Manager for eBay to CMS Matching
Handles product data loading, matching, and price history tracking
"""

import pandas as pd
import numpy as np
from datetime import datetime, date
import re
from difflib import SequenceMatcher
from typing import Dict, List, Tuple, Optional
import json
import os
import logging


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProductCatalogueManager:
    def __init__(self, catalogue_file: str = 'data/input/cms_product_catalogue.csv'):
        """Initialise the product catalogue manager"""
        self.catalogue_file = catalogue_file
        self.products_df = None
        self.price_history = []
        self.matching_patterns = {}
        self.load_catalogue()  
        
    def load_catalogue(self):
        """Load product catalogue from CSV"""
        if os.path.exists(self.catalogue_file):
            self.products_df = pd.read_csv(self.catalogue_file)
            logger.info(f"Loaded {len(self.products_df)} products from {self.catalogue_file}")
        else:
            logger.error(f"Catalogue file {self.catalogue_file} not found")
            # Create empty DataFrame WITH expected columns
            self.products_df = pd.DataFrame(columns=[
                'cms_product_code', 'cms_product_name', 
                'retail_price_inc_vat', 'retail_price_exc_vat',
                'wholesale_price', 'effective_date'
            ])
            
    def add_ebay_pattern(self, cms_code: str, pattern: str) -> None:
        """Add a matching pattern for eBay product codes"""
        if cms_code not in self.matching_patterns:
            self.matching_patterns[cms_code] = []
        self.matching_patterns[cms_code].append(pattern)
        logger.info(f"Added pattern '{pattern}' for CMS code '{cms_code}'.")
                    
    def create_search_patterns(self) -> None:
        """Create initial search patterns for product names"""
        patterns = {}
        
        for _, product in self.products_df.iterrows():
            if pd.notna(product['cms_product_name']):
                code = product['cms_product_code']
                name = product['cms_product_name']
                
                # Get base pattern of name without the trailing description
                base_pattern = name
                
                # Remove trailing indicators like 'NEW LOWER PRICE" etc
                base_pattern = re.sub(r'\s*(NEW LOWER PRICE|NEW LOWER PRICE!|NEW LOWER PRICE!!|NEW LOWER PRICE!?)\s*$', '', base_pattern, flags=re.IGNORECASE)
                base_pattern = re.sub(r'-?\sCLEARNACE.*$', '', base_pattern, flags=re.IGNORECASE)
                base_pattern = re.sub(r'-?\s*HALF PRICE.*', '', base_pattern, flags=re.IGNORECASE)
                base_pattern = re.sub(r'-?\s*BUY 1 GET 1.*', '', base_pattern, flags=re.IGNORECASE)
                base_pattern = re.sub(r'-?\s*INTRODUCTORY OFFER.*', '', base_pattern, flags=re.IGNORECASE)
                
                # Remove parenthetical information
                base_pattern = re.sub(r'\([^)]+\)', '', base_pattern)
                
                # Clean up multiple spaces
                base_pattern = ' '.join(base_pattern.split())
                
                patterns[code] = {
                    'cms_name': name,
                    'base_pattern': base_pattern,
                    'keywords': self.extract_keywords(base_pattern)
                }
                
        return patterns
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from product name"""
        # Remove common words
        stop_words = {
            'with', 'and', 'for', 'the', 'skin', 'lightening', 
            'brightening', 'whitening', 'soap', 'cream', 'lotion'
        }
        
        # Extract meaningful words
        words = re.findall(r'\w+', text.lower())
        keywords = [w for w in words if len(w) > 2 and w not in stop_words]
        
        return keywords
    
    def match_ebay_title(self, ebay_title: str, threshold: float = 0.7) -> List[Dict]:
        """
        Match eBay title to CMS products
        Returns list of matches with confidence scores
        """
        ebay_clean = self.clean_title(ebay_title)
        matches = []
        
        for _, product in self.products_df.iterrows():
            cms_name = product['cms_product_name']
            cms_code = product['cms_product_code'] if pd.notna(product['cms_product_code']) else 'NO_CODE'
            
            # Calculate similarity score
            score = self.calculate_similarity(ebay_clean, cms_name)
            
            # Check for specific product indicators
            bonus_score = 0
            
            # Size/quantity matching
            ebay_sizes = re.findall(r'\d+\s*(?:g|ml|mg)', ebay_title.lower())
            cms_sizes = re.findall(r'\d+\s*(?:g|ml|mg)', cms_name.lower())
            if ebay_sizes and cms_sizes and set(ebay_sizes) == set(cms_sizes):
                bonus_score += 0.1
            
            # Multi-pack matching
            ebay_pack = re.search(r'x\s*(\d+)', ebay_title.lower())
            cms_pack = re.search(r'x\s*(\d+)', cms_name.lower())
            if ebay_pack and cms_pack and ebay_pack.group(1) == cms_pack.group(1):
                bonus_score += 0.1
            
            final_score = min(score + bonus_score, 1.0)
            
            if final_score >= threshold:
                matches.append({
                    'cms_code': cms_code,
                    'cms_name': cms_name,
                    'confidence': final_score,
                    'wholesale_price': product['wholesale_price']
                })
        
        # Sort by confidence
        matches.sort(key=lambda x: x['confidence'], reverse=True)
        
        return matches[:5]  # Return top 5 matches
    
    def clean_title(self, title: str) -> str:
        """Clean product title for matching"""
        # Convert to lowercase
        clean = title.lower()
        
        # Remove common eBay suffixes
        clean = re.sub(r'-\s*philippines\s*$', '', clean)
        clean = re.sub(r'-\s*ph\s*$', '', clean)
        clean = re.sub(r'-\s*usa\s*$', '', clean)
        clean = re.sub(r'-\s*uk\s*$', '', clean)
        clean = re.sub(r'-\s*authentic\s*$', '', clean, flags=re.IGNORECASE)
        
        # Remove extra spaces
        clean = ' '.join(clean.split())
        
        return clean
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two product names"""
        # Clean both texts
        clean1 = self.clean_title(text1)
        clean2 = self.clean_title(text2)
        
        # Use SequenceMatcher for basic similarity
        base_score = SequenceMatcher(None, clean1, clean2).ratio()
        
        # Extract key components
        brand1 = self.extract_brand(clean1)
        brand2 = self.extract_brand(clean2)
        
        # Brand matching is crucial
        if brand1 and brand2:
            if brand1 == brand2:
                base_score += 0.2
            else:
                base_score -= 0.3
        
        return min(base_score, 1.0)
    
    def extract_brand(self, text: str) -> Optional[str]:
        """Extract brand name from product text"""
        brands = [
            'kojie san', 'belo', 'gluta-c', 'glutamax', 'silka', 
            'safeguard', 'extract', 'maxi-peel', 'skinwhite', 
            'goldilocks', 'cream silk', 'sunsilk', 'likas',
            'eskinol', 'johnsons', "johnson's", 'bench', 'ph care',
            'green cross', 'seoul white'
        ]
        
        text_lower = text.lower()
        for brand in brands:
            if brand in text_lower:
                return brand
        return None
    
    def get_price_at_date(self, cms_code: str, target_date: date) -> Dict:
        """Get the price that was effective on a specific date"""
        if cms_code not in self.products_df['cms_product_code'].values:
            return {'error': 'Product code not found'}
        
        product = self.products_df[self.products_df['cms_product_code'] == cms_code].iloc[0]
        
        # For now, return current price (extend this when you have price history)
        return {
            'cms_code': cms_code,
            'wholesale_price': product['wholesale_price'],
            'retail_price_exc_vat': product['retail_price_exc_vat'],
            'retail_price_inc_vat': product['retail_price_inc_vat'],
            'effective_date': product['effective_date']
        }
    
    def test_matching_with_ebay_data(self, ebay_csv_path: str, output_report: str = None):
        """Test matching against actual eBay sales data"""
        logger.info(f"Testing matching with eBay data from {ebay_csv_path}")
        
        # Read eBay CSV
        with open(ebay_csv_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Find header line
        header_idx = next(i for i, line in enumerate(lines) if 'Sales record number' in line)
        
        # Read data starting from header
        ebay_df = pd.read_csv(ebay_csv_path, skiprows=header_idx)
        
        # Filter to only rows with item titles
        ebay_items = ebay_df[ebay_df['Item title'].notna()].copy()
        
        # Get unique item titles
        unique_items = ebay_items['Item title'].unique()
        
        logger.info(f"Testing matching for {len(unique_items)} unique eBay items...")
        
        # Test each unique item
        results = []
        for item_title in unique_items:
            matches = self.match_ebay_title(item_title)
            
            results.append({
                'ebay_title': item_title,
                'best_match': matches[0] if matches else None,
                'confidence': matches[0]['confidence'] if matches else 0,
                'match_count': len(matches),
                'all_matches': matches
            })
        
        # Create summary report
        self._generate_matching_report(results, output_report)
        
        return results
    
    def _generate_matching_report(self, results: List[Dict], output_file: str = None):
        """Generate a matching report"""
        if output_file is None:
            output_file = f"data/reports/matching_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w') as f:
            f.write("EBAY TO CMS PRODUCT MATCHING REPORT\n")
            f.write("="*80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total items tested: {len(results)}\n\n")
            
            # Statistics
            high_confidence = sum(1 for r in results if r['confidence'] > 0.8)
            medium_confidence = sum(1 for r in results if 0.6 < r['confidence'] <= 0.8)
            low_confidence = sum(1 for r in results if 0 < r['confidence'] <= 0.6)
            no_match = sum(1 for r in results if r['confidence'] == 0)
            
            f.write("MATCHING STATISTICS:\n")
            f.write(f"High confidence (>80%):   {high_confidence} ({high_confidence/len(results)*100:.1f}%)\n")
            f.write(f"Medium confidence (60-80%): {medium_confidence} ({medium_confidence/len(results)*100:.1f}%)\n")
            f.write(f"Low confidence (<60%):    {low_confidence} ({low_confidence/len(results)*100:.1f}%)\n")
            f.write(f"No match found:           {no_match} ({no_match/len(results)*100:.1f}%)\n")
            f.write("\n" + "="*80 + "\n\n")
            
            # Detailed results
            f.write("DETAILED MATCHING RESULTS:\n\n")
            
            for i, result in enumerate(results, 1):
                f.write(f"{i}. eBay: {result['ebay_title']}\n")
                if result['best_match']:
                    f.write(f"   ✓ Match: {result['best_match']['cms_name']}\n")
                    f.write(f"   Code: {result['best_match']['cms_code']}\n")
                    f.write(f"   Confidence: {result['confidence']:.1%}\n")
                    f.write(f"   Price: £{result['best_match']['wholesale_price']}\n")
                else:
                    f.write("   ✗ No match found\n")
                f.write("\n")
        
        logger.info(f"Matching report saved to {output_file}")
    
    def export_mapping_template(self, output_file='data/reports/product_mapping_template.csv'):
        """Export a template for manual mapping review"""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Check if products_df is empty or None
        if self.products_df is None or self.products_df.empty:
            logger.warning("No products loaded. Cannot export mapping template.")
            return
        
        # Get search patterns
        patterns = self.create_search_patterns()
        
        # Create mapping dataframe
        mapping_data = []
        for code, pattern_info in patterns.items():
            mapping_data.append({
                'cms_product_code': code,
                'cms_product_name': pattern_info['cms_name'],
                'suggested_ebay_pattern': pattern_info['base_pattern'],
                'keywords': ', '.join(pattern_info['keywords']),
                'ebay_title_override': '',  # For manual input
                'amazon_title_pattern': '',  # For future use
                'notes': ''
            })
        
        # Add products without codes
        no_code_products = self.products_df[self.products_df['cms_product_code'].isna()]
        for _, product in no_code_products.iterrows():
            mapping_data.append({
                'cms_product_code': 'NEEDS_CODE',
                'cms_product_name': product['cms_product_name'],
                'suggested_ebay_pattern': product['cms_product_name'],
                'keywords': ', '.join(self.extract_keywords(product['cms_product_name'])),
                'ebay_title_override': '',
                'amazon_title_pattern': '',
                'notes': 'Product needs code assignment'
            })
        
        mapping_df = pd.DataFrame(mapping_data)
        mapping_df.to_csv(output_file, index=False)
        logger.info(f"Exported mapping template to {output_file}")
        logger.info("You can edit this file to improve matching patterns")
    
    def update_price(self, cms_code: str, new_price: float, effective_date: str = None):
        """Update product price with effective date"""
        if effective_date is None:
            effective_date = datetime.now().strftime('%Y-%m-%d')
        
        # Update in main dataframe
        mask = self.products_df['cms_product_code'] == cms_code
        if mask.any():
            # Store old price in history
            old_price = self.products_df.loc[mask, 'wholesale_price'].values[0]
            self.price_history.append({
                'cms_code': cms_code,
                'old_price': old_price,
                'new_price': new_price,
                'changed_date': effective_date
            })
            
            # Update current price
            self.products_df.loc[mask, 'wholesale_price'] = new_price
            self.products_df.loc[mask, 'effective_date'] = effective_date
            
            # Save to CSV
            self.products_df.to_csv(self.catalogue_file, index=False)
            logger.info(f"Updated price for {cms_code}: £{old_price} → £{new_price} (effective {effective_date})")
        else:
            logger.error(f"Product code {cms_code} not found")
    
    def add_product_mapping(self, mapping_file='config/product_mappings.json'):
        """Load custom product mappings from JSON file"""
        if os.path.exists(mapping_file):
            with open(mapping_file, 'r') as f:
                mappings = json.load(f)
            
            for cms_code, patterns in mappings.items():
                for pattern in patterns:
                    self.add_ebay_pattern(cms_code, pattern)
            
            logger.info(f"Loaded {len(mappings)} product mappings from {mapping_file}")
        else:
            logger.warning(f"Mapping file {mapping_file} not found")


# Example usage and testing
if __name__ == "__main__":
    # Initialise catalogue manager
    catalogue = ProductCatalogueManager()
    
    # Export mapping template for review
    catalogue.export_mapping_template()
    
    # Test with sample eBay titles
    test_titles = [
        "Kojie San Soap 100g x 3 (Large Trio Pack) - Skin Brightening & Lightening",
        "Gluta-C Kojic Plus Lightening Soap Glutathione & Vit C - 60g x 2 (Double Pack)",
        "Belo Intensive Kojic Acid & Tranexamic Acid Bar Soap - 65g x 3 (Triple Pack)",
        "Extract Papaya Calamansi Soap 125g - PHILIPPINES",
        "Silka Papaya Lotion 500ml (Large Size) - Skin Brightening"
    ]
    
    print("\n\nTesting sample eBay titles:")
    print("="*80)
    for title in test_titles:
        matches = catalogue.match_ebay_title(title)
        print(f"\neBay: {title}")
        if matches:
            best = matches[0]
            print(f"  Match: {best['cms_name']}")
            print(f"  Code: {best['cms_code']}")
            print(f"  Confidence: {best['confidence']:.2%}")
            print(f"  Price: £{best['wholesale_price']}")
        else:
            print("  No match found")
    
    # If you have the eBay CSV file, uncomment this:
    # catalogue.test_matching_with_ebay_data('data/input/eBayOrdersReportAug132025143A493A20070013243478577.csv')
                