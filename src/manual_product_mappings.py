# manual_product_mappings.py
"""
Manual product mappings and special handling rules
"""

# Manual cost mappings for products not in catalogue
MANUAL_COST_MAPPINGS = {
    # Dr. S. Wong products
    "dr. s. wong's sulfur soap 80g": 1.10,
    "dr. s. wong's sulfur moisturising soap 80g": 1.18,
    
    # Renew Placenta products
    "renew placenta classic herbal beauty soap 135g": 2.50,
    "renew placenta white herbal beauty soap 135g": 2.50,
    
    # C.Y. Gabriel products (non-kojic)
    "c. y. gabriel special pink soap 135g": 1.14,
    "c. y. gabriel special soap": 1.14,  # Default for other C.Y. Gabriel
    
    # C.Y. Gabriel Kojic
    "c. y. gabriel kojic soap 135g": 1.61,
    
    # Closeup toothpaste
    "closeup toothpaste": 3.31,  # Default for any Closeup toothpaste
}

# Products that should be grouped as "Assorted Cosmetics"
ASSORTED_COSMETICS_BRANDS = [
    "flawlessly u",
    "flawlessly you"
]

# Special matching rules - map eBay patterns to CMS products
SPECIAL_MATCHING_RULES = {
    # Gluta-C variations
    "gluta lotion.*spf.*300ml": "Gluta-C Skin Lightening & Brightening Body Lotion 300ml",
    "gluta kojic body lotion.*spf.*300ml": "Gluta-C with Kojic Plus Skin Lightening & Brightening Body Lotion 300ml",
}

# Flawlessly U box pricing from the image
FLAWLESSLY_U_BOX_PRICES = {
    "papaya calamansi soap 125g x 72": {"box_price": 97.230, "units": 72},
    "green papaya calamansi soap 125g x 72": {"box_price": 111.560, "units": 72},
    "kojic + glutathione soap (65g x 2) x 48": {"box_price": 81.680, "units": 48},
    "papaya calamansi lotion 500ml with pump x 12": {"box_price": 88.520, "units": 12},
}

def get_manual_cost(product_name: str) -> float:
    """
    Get manual cost for products not in catalogue
    """
    product_lower = product_name.lower()
    
    # Check direct mappings
    for pattern, cost in MANUAL_COST_MAPPINGS.items():
        if pattern in product_lower:
            return cost
    
    # Special cases
    if "closeup" in product_lower and "toothpaste" in product_lower:
        return MANUAL_COST_MAPPINGS["closeup toothpaste"]
    
    if "c. y. gabriel" in product_lower or "c.y. gabriel" in product_lower:
        if "kojic" in product_lower:
            return MANUAL_COST_MAPPINGS["c. y. gabriel kojic soap 135g"]
        else:
            return MANUAL_COST_MAPPINGS["c. y. gabriel special soap"]
    
    return None

def is_assorted_cosmetics(product_name: str) -> bool:
    """
    Check if product should be grouped as Assorted Cosmetics
    """
    product_lower = product_name.lower()
    return any(brand in product_lower for brand in ASSORTED_COSMETICS_BRANDS)

def get_flawlessly_u_unit_cost(product_name: str) -> float:
    """
    Calculate unit cost for Flawlessly U products from box pricing
    """
    product_lower = product_name.lower()
    
    # Try to match with box configurations
    for box_config, pricing in FLAWLESSLY_U_BOX_PRICES.items():
        # Create a flexible pattern from the box config
        key_parts = box_config.split()
        
        # Check if main product identifiers match
        if "papaya calamansi soap" in product_lower and "papaya calamansi soap" in box_config:
            if "green" in product_lower and "green" in box_config:
                return pricing["box_price"] / pricing["units"]
            elif "green" not in product_lower and "green" not in box_config:
                return pricing["box_price"] / pricing["units"]
                
        elif "kojic" in product_lower and "glutathione" in product_lower and "kojic + glutathione" in box_config:
            return pricing["box_price"] / pricing["units"]
            
        elif "papaya calamansi lotion" in product_lower and "pump" in product_lower and "papaya calamansi lotion" in box_config:
            return pricing["box_price"] / pricing["units"]
    
    # Default cost if no match found
    return 1.50  # Default fallback

def apply_special_matching_rule(ebay_title: str) -> str:
    """
    Apply special matching rules to find CMS product name
    """
    ebay_lower = ebay_title.lower()
    
    for pattern, cms_name in SPECIAL_MATCHING_RULES.items():
        # Convert pattern to regex
        import re
        if re.search(pattern, ebay_lower):
            return cms_name
    
    return None