"""
Entity normalization mapping
Maps common variations to canonical names
"""

# Known REITs and Major Buyers
KNOWN_BUYERS = {
    "welltower": "Welltower",
    "welltower inc": "Welltower",
    "welltower inc.": "Welltower",
    "well": "Welltower",
    
    "ventas": "Ventas",
    "ventas inc": "Ventas",
    "ventas inc.": "Ventas",
    
    "healthpeak": "Healthpeak Properties",
    "healthpeak properties": "Healthpeak Properties",
    "healthpeak properties inc": "Healthpeak Properties",
    
    "omega healthcare": "Omega Healthcare Investors",
    "omega healthcare investors": "Omega Healthcare Investors",
    "omega": "Omega Healthcare Investors",
    
    "sabra": "Sabra Health Care REIT",
    "sabra health care": "Sabra Health Care REIT",
    "sabra health care reit": "Sabra Health Care REIT",
    
    "nhi": "National Health Investors",
    "national health investors": "National Health Investors",
    
    "ltc properties": "LTC Properties",
    "ltc": "LTC Properties",
    
    "physicians realty": "Physicians Realty Trust",
    "physicians realty trust": "Physicians Realty Trust",
    
    "healthcare trust": "Healthcare Trust",
    "healthcare realty trust": "Healthcare Realty Trust",
}

# Known Operators
KNOWN_OPERATORS = {
    "brookdale": "Brookdale Senior Living",
    "brookdale senior living": "Brookdale Senior Living",
    
    "five star": "Five Star Senior Living",
    "five star senior living": "Five Star Senior Living",
    
    "atria": "Atria Senior Living",
    "atria senior living": "Atria Senior Living",
    
    "sunrise": "Sunrise Senior Living",
    "sunrise senior living": "Sunrise Senior Living",
    
    "benchmark": "Benchmark Senior Living",
    "benchmark senior living": "Benchmark Senior Living",
    
    "discovery": "Discovery Senior Living",
    "discovery senior living": "Discovery Senior Living",
    
    "capital senior living": "Capital Senior Living",
    
    "holiday retirement": "Holiday Retirement",
}

# Combine all
ALL_ENTITIES = {**KNOWN_BUYERS, **KNOWN_OPERATORS}

def normalize_entity_name(name):
    """
    Normalize an entity name to its canonical form
    
    Args:
        name: Raw company name from article
        
    Returns:
        Normalized canonical name, or original if not in mapping
    """
    if not name or name == 'N/A':
        return 'N/A'
    
    # Clean the name
    clean = name.lower().strip()
    
    # Remove common suffixes
    suffixes = [', inc.', ' inc.', ', inc', ' inc', 
                ', llc', ' llc', ', ltd', ' ltd',
                ', corp', ' corp', ', corporation', ' corporation']
    
    for suffix in suffixes:
        if clean.endswith(suffix):
            clean = clean[:-len(suffix)].strip()
    
    # Look up in mapping
    if clean in ALL_ENTITIES:
        return ALL_ENTITIES[clean]
    
    # If not found, return title case version of cleaned name
    return name.replace(', Inc.', '').replace(' Inc.', '').replace(', LLC', '').replace(' LLC', '').strip()

def add_entity_mapping(variations, canonical_name):
    """
    Add a new entity mapping
    
    Args:
        variations: List of variations (e.g., ["company inc", "company llc"])
        canonical_name: The canonical name to use (e.g., "Company Name")
    """
    for variation in variations:
        ALL_ENTITIES[variation.lower().strip()] = canonical_name

# Examples of how to add new entities as you discover them:
# add_entity_mapping(["new company inc", "new co"], "New Company")
