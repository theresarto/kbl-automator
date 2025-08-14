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
        
    def load_catalogue(self) -> None:
        """Load product catalogue from CSV file"""    
        if os.path.exists(self.catalogue_file):
            self.products_df = pd.read_csv(self.catalogue_file)
            logger.info(f"Catalogue loaded with {len(self.products_df)} products.")
        else:
            logger.error(f"Catalogue file {self.catalogue_file} does not exist.")
            # Create empty DataFrame if file does not exist
            self.products_df = pd.DataFrame(columns=[
                'cms_product_code', 'cms_product_name',
                'retail_price_inc_vat', 'retail_price_ex_vat',
                'wholesale_price', 'effective_date'
            ])
            