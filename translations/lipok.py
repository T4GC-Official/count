# Main Categories
FOOD = "food"
HOUSEHOLD = "household"
FUEL = "fuel"

# Food Subcategories
VEGETABLES = "vegetables"
FRUITS = "fruits"
MEATS = "meats"
RICE = "rice"
MILLETS = "millets"
WHEAT = "wheat"
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
    MILLETS: "🌾",
    WHEAT: "🌾",
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
    MILLETS: "Millets",
    WHEAT: "Wheat",
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


TRANSLATIONS_MARATHI = {
    # Main Categories
    FOOD: "खाद्यपदार्थ",
    HOUSEHOLD: "गृह वस्तुं",
    FUEL: "ईंधन",

    # Food Subcategories
    VEGETABLES: "भाज्या",
    FRUITS: "फळे",
    MEATS: "मांसाहार",
    RICE: "तांदूळ",
    MILLETS: "नाचणी/ बाजरी/ ज्वारी",
    WHEAT: "गहू",
    DAIRY: "दुग्धजन्य पदार्थ",

    # Household Subcategories
    SOAP: "साबण",
    CLOTHES: "कपडे",
    STATIONARY: "स्टेशनरी",
    COSMETICS: "सौंदर्यप्रसाधने",

    # Fuel Subcategories
    PETROL: "पेट्रोल",
    GAS: "गॅस",
    DIESEL: "डिझेल",

    # Source Options
    WITHIN_VILLAGE: "गावात उत्पादित?",
    OUTSIDE_VILLAGE: "गावाबाहेर उत्पादित?",

    # Price Ranges
    PRICE_0_50: "0-50",
    PRICE_50_100: "50-100",
    PRICE_100_200: "100-200",
    PRICE_CUSTOM: "विशेष",
}


def get_button_text(key: str, language: str = "mr") -> str:
    """Get button text with emoji if available"""
    if language == "en":
        text = TRANSLATIONS[key]
    elif language == "mr":
        text = TRANSLATIONS_MARATHI[key]
    else:
        raise ValueError(f"Invalid language: {language}")

    emoji = EMOJI.get(key, "")
    return f"{text} {emoji}".strip()
