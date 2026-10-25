"""The sample menu lives here. There is no database or saved customer data."""

MENU_ITEMS = [
    {"name": "Cloud Nine Latte", "description": "Smooth espresso, steamed milk, and a little cloud of foam.", "category": "Coffee", "price": 4.50},
    {"name": "Classic Cappuccino", "description": "Rich espresso with equal parts warm milk and airy foam.", "category": "Coffee", "price": 4.00},
    {"name": "Slow Morning Americano", "description": "A double espresso softened with hot water. Simply lovely.", "category": "Coffee", "price": 3.25},
    {"name": "Garden Green Tea", "description": "A delicate green tea with a fresh, gently grassy finish.", "category": "Tea", "price": 3.00},
    {"name": "Cozy Chai", "description": "Black tea, warm spices, and steamed milk in a comforting cup.", "category": "Tea", "price": 4.25},
    {"name": "Butter Croissant", "description": "Golden, flaky layers with a soft and buttery center.", "category": "Snacks", "price": 3.50},
    {"name": "Blueberry Muffin", "description": "A tender little bake filled with sweet, juicy blueberries.", "category": "Snacks", "price": 3.75},
    {"name": "Chocolate Chip Cookie", "description": "Crisp at the edges, soft in the middle, full of chocolate.", "category": "Snacks", "price": 2.75},
]


def get_menu():
    """Return the menu. Replace this function during a future database lesson."""
    return [item.copy() for item in MENU_ITEMS]
