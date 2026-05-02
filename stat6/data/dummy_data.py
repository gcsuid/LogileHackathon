# -----------------------------
# SAMPLE RECIPE DATA (APPROVED)
# -----------------------------

SAMPLE_RECIPE = {
    "name": "Spicy Paneer Wrap",
    "category": "food",  # explicitly allowed now
    "yield": 10,
    "ingredients": [
        {"name": "paneer", "quantity": 0.8, "unit": "kg"},
        {"name": "tortilla", "quantity": 10, "unit": "piece"},
        {"name": "onion", "quantity": 0.4, "unit": "kg"},
        {"name": "capsicum", "quantity": 0.5, "unit": "kg"},
        {"name": "sauce", "quantity": 0.15, "unit": "kg"},
        {"name": "cheese", "quantity": 0.2, "unit": "kg"},
    ],
    "steps": [
        "Slice paneer and vegetables.",
        "Saute paneer with onion, capsicum, and sauce.",
        "Warm tortillas and assemble the wraps with cheese.",
    ],
    "equipment": ["stove", "pan", "knife", "cutting_board", "grill"],
}


# -----------------------------
# INGREDIENT PRICING (per unit)
# -----------------------------

INGREDIENT_PRICES = {
    "paneer": 280.0,     # per kg
    "tortilla": 12.0,    # per piece
    "onion": 40.0,       # per kg
    "capsicum": 90.0,    # per kg
    "sauce": 160.0,      # per kg
    "cheese": 420.0,     # per kg
}


# -----------------------------
# STORE CAPABILITIES
# -----------------------------

STORE_EQUIPMENT = {
    "store_name": "Downtown Express Store",
    "equipment": ["stove", "pan", "knife", "cutting_board", "grill"],
}

EQUIPMENT_CATALOG = {
    "stove": {
        "display_name": "Stove",
        "capabilities": ["heat", "saute", "cooktop"],
        "daily_operating_cost": 120.0,
    },
    "pan": {
        "display_name": "Pan",
        "capabilities": ["saute", "shallow_cook"],
        "daily_operating_cost": 40.0,
    },
    "knife": {
        "display_name": "Knife",
        "capabilities": ["cut", "prep"],
        "daily_operating_cost": 10.0,
    },
    "cutting_board": {
        "display_name": "Cutting Board",
        "capabilities": ["prep_surface"],
        "daily_operating_cost": 8.0,
    },
    "grill": {
        "display_name": "Grill",
        "capabilities": ["direct_heat", "char", "finish_wrap"],
        "daily_operating_cost": 160.0,
    },
    "grill_pan": {
        "display_name": "Grill Pan",
        "capabilities": ["direct_heat", "finish_wrap"],
        "daily_operating_cost": 90.0,
    },
    "flat_top": {
        "display_name": "Flat Top",
        "capabilities": ["direct_heat", "finish_wrap", "batch_heat"],
        "daily_operating_cost": 140.0,
    },
    "oven": {
        "display_name": "Oven",
        "capabilities": ["batch_heat", "finish_wrap"],
        "daily_operating_cost": 180.0,
    },
}

EQUIPMENT_SUBSTITUTIONS = {
    "grill": ["grill_pan", "flat_top", "oven"],
}

STORE_EQUIPMENT_INVENTORY = {
    "Downtown Express Store": {
        "stove": {"available": True},
        "pan": {"available": True},
        "knife": {"available": True},
        "cutting_board": {"available": True},
        "grill": {"available": True},
        "grill_pan": {"available": True},
        "flat_top": {"available": False},
        "oven": {"available": False},
    }
}


# -----------------------------
# BUSINESS CONSTRAINTS
# -----------------------------

MAX_BATCH_COST_ALLOWED = 700.0
TARGET_SELLING_PRICE = 900.0


# -----------------------------
# POLICY CONFIG
# -----------------------------

ALLOWED_CATEGORIES = ["food", "beverage", "retail"]
