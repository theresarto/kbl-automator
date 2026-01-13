# manual_product_mappings.py - Enhanced Version
"""
Enhanced manual product mappings with complete fixes for all matching issues
"""
import re

# Manual cost mappings with CMS names for web scraping
MANUAL_COST_MAPPINGS = {
    # Dr. S. Wong products
    "dr. s. wong's sulfur soap 80g": {
        "cost": 1.10,
        "cms_name": "Dr S. Wong's Sulfur Soap 80g"
    },
    "dr. s. wong's sulfur moisturising soap 80g": {
        "cost": 1.18,
        "cms_name": "Dr S. Wong's Sulfur Soap with Moisturizer 80g"
    },
    
    # Renew Placenta products
    "renew placenta classic herbal beauty soap 135g": {
        "cost": 2.50,
        "cms_name": "Renew Placenta Classic Herbal Beauty Soap 135g"
    },
    "renew placenta white herbal beauty soap 135g": {
        "cost": 2.50,
        "cms_name": "Renew Placenta White Skin Lightening Soap 135g"
    },
    
    # C.Y. Gabriel products
    "c. y. gabriel special pink soap 135g": {
        "cost": 1.14,
        "cms_name": "C.Y. Gabriel Special Pink Lightening & Brightening Beauty Soap 135g"
    },
    "c. y. gabriel special green soap 135g": {
        "cost": 1.14,
        "cms_name": "C.Y. Gabriel Special Green Lightening & Brightening Beauty Soap 135g"
    },
    "c. y. gabriel papaya soap 135g": {
        "cost": 1.14,
        "cms_name": "C.Y. Gabriel Papaya Lightening & Brightening Beauty Soap 135g"
    },
    "c. y. gabriel kojic soap 135g": {
        "cost": 1.61,
        "cms_name": "C.Y. Gabriel Kojic with Glutathione Skin Lightening & Brightening Soap 135g"
    },
    
    # Closeup toothpaste
    "closeup red hot toothpaste": {
        "cost": 3.31,
        "cms_name": "Closeup Red Hot Toothpaste 95ml (PH)"
    },
    "closeup menthol fresh toothpaste": {
        "cost": 3.31,
        "cms_name": "Closeup Menthol Fresh Toothpaste 95ml (PH)"
    },
    "closeup ever fresh toothpaste": {
        "cost": 3.31,
        "cms_name": "Closeup Menthol Fresh Toothpaste 95ml (PH)"  # Map to menthol
    },
    
    # GlutaMAX Men
    "glutamax men total oil control facial face wash 100g": {
        "cost": 4.20,
        "cms_name": "GlutaMAX Men Facial Wash 100g"
    },
    
    # Kojie San 45g special variant
    "kojie san soap 45g": {
        "cost": 0.81,
        "cms_name": "Kojie San Soap 45g"
    }
}

# Special matching rules - enhanced with all fixes
SPECIAL_MATCHING_RULES = {
    # Belo Kojic Acid variants
    r"belo.*kojic.*tranexamic.*bar.*65g\s*x\s*3": "Belo Kojic Acid & Tranexamic Acid Intensive Lightening & Brightening Bar 65g x 2 + 1 FREE",
    r"belo.*kojic.*tranexamic.*extra moisture.*65g\s*x\s*2": "Belo Kojic Acid & Tranexamic Acid EXTRA MOISTURE Bar 65g x 2",
    r"belo.*kojic.*tranexamic.*body wash.*475ml": "Belo Kojic Acid & Tranexamic Acid Skin Lightening & Brightening Body Wash 475ml",
    
    # Gluta-C specific products
    r"gluta-c.*facial.*toner.*100ml": "Gluta-C Skin Lightening & Brightening Facial Toner 100ml",
    r"gluta-c.*facial.*night.*30ml": "Gluta-C Skin Lightening & Brightening Facial NIGHT REPAIR Serum 30ml",
    r"gluta-c.*facial.*day.*cream.*30ml": "Gluta-C Skin Lightening & Brightening Facial DAY Cream 30ml",
    r"gluta\s*lotion.*spf.*300ml": "Gluta-C Skin Lightening & Brightening Body Lotion 300ml",
    r"gluta.*kojic.*body lotion.*spf.*300ml": "Gluta-C with Kojic Plus Skin Lightening & Brightening Body Lotion 300ml",
    
    # Kojie San body products
    r"kojie san.*body lotion.*spf25.*250": "Kojie San KOJIC Skin Lightening & Brightening Lotion SPF25 250ml",
    r"kojie san.*body wash.*300ml": "Kojie San Skin Lightening Body Wash 300ml",
    r"kojie san.*facial.*wash.*100g": "Kojie San Skin Lightening & Brightening Facial Wash 100g",
    
    # Belo Papaya
    r"belo.*papaya.*soap.*65g\s*x\s*3": "Belo Essentials Skin Lightening & Brightening Papaya Soap 65g x 2 + 1 FREE",
    r"belo.*papaya.*body lotion.*spf30.*200ml": "Belo Essentials Skin Lightening & Brightening Papaya Lotion with SPF30 200ml",
    r"belo.*skin hydrating.*toner.*100ml": "Belo Essentials Skin Hydrating Lightening & Brightening TONER 100ml",
    
    # GlutaMAX
    r"glutamax.*moisturi[sz]ing.*lotion.*90ml": "GlutaMax Lightening & Moisturizing Lotion 90ml",
    
    # Seoul White
    r"seoul white.*120g\s*x\s*3": "Seoul White Korea Double White Intense Bright Kojic Arbutin 120g x2 + 1 Free",

    # Silka Premium Body Wash
    r"silka.*premium.*body wash.*500ml": "Silka Papaya Luxe Lightening Body Wash 500ml",
    
    # Silka Orange - ignore orange and match regular
    r"silka.*papaya.*soap.*90g\s*x\s*3": "Silka Papaya Skin Lightening & brightening Soap 3 x 90g Soap (Triple Pack)",
    
    # ---- AMAZON-SPECIFIC RULES ---- #

    # Amazon-specific product mappings
    r"glupa glutathione.*whitening soap.*135g": "Glupa Glutathione & Papaya Skin Lightening & Brightening Soap 135g - NEW LOWER PRICE!",
    r"gluta c kojic plus face and neck cream": "Gluta-C with Kojic Plus Lightening & Brightening Face & Neck Cream 25g",
    r"gluta-c facial day cream": "Gluta-C Skin Lightening & Brightening Facial DAY Cream 30ml",
    r"papaya calamansi extract whitening soap": "Extract Skin Lightening & Brightening Herbal Soap Papaya Calamansi 125g",
    r"kojie san.*lightening.*soap.*3 bars.*100g": "Kojie San Skin Lightening & Brightening Soap 100g x 3",
    r"4 pack extract papaya calamansi": "Extract Skin Lightening & Brightening Herbal Soap Papaya Calamansi 125g",
    r"assorted eskinol facial scrub": "Eskinol CLASSIC Lightening & Brightening Face Cleanser 225ml",
    r"gluta-c.*underarm.*bikini.*whitening.*gel.*cream": "Gluta-C Intense Lightening & Brightening Underarm & Bikini Gel 20ml",
}

# Products that should be grouped as "Assorted Cosmetics"
ASSORTED_COSMETICS_BRANDS = [
    "flawlessly u",
    "flawlessly you"
]

# Flawlessly U box pricing
FLAWLESSLY_U_BOX_PRICES = {
    "papaya calamansi soap 125g": {"box_price": 97.230, "units": 72},
    "green papaya calamansi soap 125g": {"box_price": 111.560, "units": 72},
    "kojic glutathione soap 65g": {"box_price": 81.680, "units": 48},  # 65g x 2 per unit
    "papaya calamansi lotion 500ml pump": {"box_price": 88.520, "units": 12},
}

def parse_bracket_selection(ebay_title: str) -> tuple:
    """
    Parse bracket notation at end of title
    Returns: (cleaned_title, selected_variant)
    """
    # Look for [...] at the end
    bracket_match = re.search(r'\[([^\]]+)\]$', ebay_title)
    if bracket_match:
        variant = bracket_match.group(1)
        cleaned_title = ebay_title[:bracket_match.start()].strip()
        return cleaned_title, variant
    return ebay_title, None

def normalize_product_type(title: str):
    """Extract and normalize product type"""
    title_lower = title.lower()
    
    # Define product type patterns
    types = {
        'soap': r'\bsoap\b',
        'lotion': r'\blotion\b',
        'toner': r'\btoner\b',
        'face wash': r'\b(face\s*wash|facial\s*wash)\b',
        'body wash': r'\bbody\s*wash\b',
        'cream': r'\b(cream|creme)\b',
        'deodorant': r'\bdeodorant\b',
        'cleanser': r'\bcleanser\b',
        'serum': r'\bserum\b'
    }
    
    for type_name, pattern in types.items():
        if re.search(pattern, title_lower):
            return type_name
    return None

def extract_size_and_quantity(title: str) -> dict:
    """Extract size and quantity information"""
    result = {
        'size': None,
        'quantity': None,
        'is_multipack': False
    }
    
    # Extract size (e.g., 135g, 100ml)
    size_match = re.search(r'(\d+)\s*(g|ml|mg)', title.lower())
    if size_match:
        result['size'] = f"{size_match.group(1)}{size_match.group(2)}"
    
    # Extract quantity (e.g., x 3, x2)
    qty_match = re.search(r'x\s*(\d+)', title.lower())
    if qty_match:
        result['quantity'] = int(qty_match.group(1))
        result['is_multipack'] = True
    
    return result

def get_manual_cost(product_name: str):
    """Get manual cost and CMS name for products not in catalogue"""
    product_lower = product_name.lower()
    
    # Check direct mappings
    for pattern, info in MANUAL_COST_MAPPINGS.items():
        if pattern in product_lower:
            return info
    
    # Special cases
    if "closeup" in product_lower and "toothpaste" in product_lower:
        if "red hot" in product_lower:
            return MANUAL_COST_MAPPINGS["closeup red hot toothpaste"]
        elif "menthol" in product_lower or "ever fresh" in product_lower:
            return MANUAL_COST_MAPPINGS["closeup menthol fresh toothpaste"]
    
    if "c. y. gabriel" in product_lower or "c.y. gabriel" in product_lower:
        if "kojic" in product_lower:
            return MANUAL_COST_MAPPINGS["c. y. gabriel kojic soap 135g"]
        elif "pink" in product_lower:
            return MANUAL_COST_MAPPINGS["c. y. gabriel special pink soap 135g"]
        elif "green" in product_lower:
            return MANUAL_COST_MAPPINGS["c. y. gabriel special green soap 135g"]
        elif "papaya" in product_lower:
            return MANUAL_COST_MAPPINGS["c. y. gabriel papaya soap 135g"]
    
    # Bundle handling
    if "safeguard bundle pack" in product_lower and "125g" in product_lower:
        # Count how many variants mentioned
        count = len(re.findall(r'(pure white|fresh green|floral pink)', product_lower))
        if count > 1:
            return {"cost": 1.52 * count, "cms_name": f"Safeguard Bundle Pack {count} bars"}
    
    return None

def is_assorted_cosmetics(product_name: str) -> bool:
    """Check if product should be grouped as Assorted Cosmetics"""
    product_lower = product_name.lower()
    return any(brand in product_lower for brand in ASSORTED_COSMETICS_BRANDS)

def get_flawlessly_u_unit_cost(product_name: str) -> float:
    """Calculate unit cost for Flawlessly U products from box pricing"""
    product_lower = product_name.lower()
    
    # Determine product type
    if "soap" in product_lower:
        if "green papaya" in product_lower:
            return FLAWLESSLY_U_BOX_PRICES["green papaya calamansi soap 125g"]["box_price"] / FLAWLESSLY_U_BOX_PRICES["green papaya calamansi soap 125g"]["units"]
        elif "kojic" in product_lower and "glutathione" in product_lower:
            # Note: box contains 48 units of (65g x 2)
            return FLAWLESSLY_U_BOX_PRICES["kojic glutathione soap 65g"]["box_price"] / (FLAWLESSLY_U_BOX_PRICES["kojic glutathione soap 65g"]["units"] * 2)
        else:
            return FLAWLESSLY_U_BOX_PRICES["papaya calamansi soap 125g"]["box_price"] / FLAWLESSLY_U_BOX_PRICES["papaya calamansi soap 125g"]["units"]
    elif "lotion" in product_lower and "pump" in product_lower:
        return FLAWLESSLY_U_BOX_PRICES["papaya calamansi lotion 500ml pump"]["box_price"] / FLAWLESSLY_U_BOX_PRICES["papaya calamansi lotion 500ml pump"]["units"]
    
    # Default fallback
    return 1.50

def apply_special_matching_rule(ebay_title: str):
    """Apply special matching rules to find CMS product name"""
    ebay_lower = ebay_title.lower()
    
    for pattern, cms_name in SPECIAL_MATCHING_RULES.items():
        if re.search(pattern, ebay_lower):
            return cms_name
    
    return None

def should_match_variant(ebay_title: str, cms_name: str, variant: str) -> bool:
    """Check if a specific variant should be matched"""
    ebay_lower = ebay_title.lower()
    cms_lower = cms_name.lower()
    variant_lower = variant.lower()
    
    # GREEN variant - only match if explicitly mentioned
    if variant_lower == "green":
        return "green" in ebay_lower
    
    # PUMP variant - only for Silka lotions
    if variant_lower == "pump" or "with pump" in cms_lower:
        return "pump" in ebay_lower and "lotion" in ebay_lower and "silka" in ebay_lower
    
    # HydroMoist variant
    if "hydromoist" in cms_lower:
        return "hydromoist" in ebay_lower or "hydro moist" in ebay_lower
    
    # Dream White variant
    if "dream white" in cms_lower:
        return "dream white" in ebay_lower or "dreamwhite" in ebay_lower
    
    return True

# Add these at the END of manual_product_mappings.py

def handle_product_sets(ebay_title: str):
    """
    Handle product sets (e.g., SOAP & LOTION set)
    Returns list of individual products if it's a set
    """
    title_lower = ebay_title.lower()
    
    # Check for Extract sets
    if "extract" in title_lower and "&" in title_lower and "set" in title_lower:
        products = []
        
        if "soap" in title_lower and "125g" in title_lower:
            products.append({
                'name': "Extract Skin Lightening & Brightening Herbal Soap Papaya Calamansi 125g",
                'type': 'soap'
            })
        
        if "lotion" in title_lower and "200ml" in title_lower:
            products.append({
                'name': "Extract Lightening & Brightening Papaya Calamansi Lotion 200ml",
                'type': 'lotion'
            })
        
        return products
    
    return None

def clean_silka_title(title: str) -> str:
    """Remove 'Orange' from Silka product titles"""
    if "silka" in title.lower() and "orange" in title.lower():
        # Remove 'Orange' but keep everything else
        title = re.sub(r'\borange\s+', '', title, flags=re.IGNORECASE)
    return title