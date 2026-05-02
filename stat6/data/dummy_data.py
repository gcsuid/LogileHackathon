SAMPLE_RECIPE = {
    "name": "Spicy Paneer Wrap",
    "yield": 10,
    "ingredients": [
        {"name": "paneer", "quantity": 1.2, "unit": "kg"},
        {"name": "tortilla", "quantity": 10, "unit": "piece"},
        {"name": "onion", "quantity": 0.4, "unit": "kg"},
        {"name": "capsicum", "quantity": 0.5, "unit": "kg"},
        {"name": "sauce", "quantity": 0.25, "unit": "kg"},
        {"name": "cheese", "quantity": 0.3, "unit": "kg"},
    ],
    "steps": [
        "Slice paneer and vegetables.",
        "Saute paneer with onion, capsicum, and sauce.",
        "Warm tortillas and assemble the wraps with cheese.",
    ],
    "equipment": ["stove", "pan", "knife", "cutting_board", "grill"],
}

INGREDIENT_PRICES = {
    "paneer": 280.0,
    "tortilla": 12.0,
    "onion": 40.0,
    "capsicum": 90.0,
    "sauce": 160.0,
    "cheese": 420.0,
}

STORE_EQUIPMENT = {
    "store_name": "Downtown Express Store",
    "equipment": ["stove", "pan", "knife", "cutting_board"],
}

MAX_BATCH_COST_ALLOWED = 520.0
TARGET_SELLING_PRICE = 650.0
