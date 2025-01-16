# Main Categories
FOOD = "food"
HOUSEHOLD = "household"
FUEL = "fuel"

# Food Subcategories
VEGETABLES = "vegetables"
FRUITS = "fruits"
MEATS = "meats"
RICE = "rice"
DAIRY = "dairy"

# Household Subcategories
SOAP = "soap"
CLOTHES = "clothes"
STATIONARY = "stationary"
COSMETICS = "cosmetics"

# Fuel Subcategories
PETROL = "petrol"
GAS = "gas"
DIESEL = "diesel"

# Source Options
WITHIN_VILLAGE = "within"
OUTSIDE_VILLAGE = "outside"

# Price Ranges
PRICE_0_50 = "0-50"
PRICE_50_100 = "50-100"
PRICE_100_200 = "100-200"
PRICE_CUSTOM = "custom"

# Emojis
EMOJI = {
    FOOD: "🥘",
    HOUSEHOLD: "🏠",
    FUEL: "⛽",
    VEGETABLES: "🥔🍅",
    FRUITS: "🍌🍉",
    MEATS: "🍗🥚",
    RICE: "🍚",
    DAIRY: "🐮🥛",
    SOAP: "🧼",
    CLOTHES: "👚👖",
    STATIONARY: "📚📝",
    COSMETICS: "💄",
    PETROL: "⛽",
    GAS: "⛽",
    DIESEL: "🛢️",
}

# Translations
TRANSLATIONS = {
    # Main Categories
    FOOD: "Food",
    HOUSEHOLD: "Household Items",
    FUEL: "Fuel",

    # Food Subcategories
    VEGETABLES: "Vegetables",
    FRUITS: "Fruits",
    MEATS: "Meats",
    RICE: "Rice",
    DAIRY: "Dairy Products",

    # Household Subcategories
    SOAP: "Soap",
    CLOTHES: "Clothes",
    STATIONARY: "Stationary",
    COSMETICS: "Cosmetics",

    # Fuel Subcategories
    PETROL: "Petrol",
    GAS: "Gas",
    DIESEL: "Diesel",

    # Source Options
    WITHIN_VILLAGE: "Produced within the village",
    OUTSIDE_VILLAGE: "Produced outside the village",

    # Price Ranges
    PRICE_0_50: "0-50",
    PRICE_50_100: "50-100",
    PRICE_100_200: "100-200",
    PRICE_CUSTOM: "Custom",
}


def get_button_text(key: str) -> str:
    """Get button text with emoji if available"""
    text = TRANSLATIONS[key]
    emoji = EMOJI.get(key, "")
    return f"{text} {emoji}".strip()
