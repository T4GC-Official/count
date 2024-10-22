# Message to display on chat start.
FINANCE_START_MSG = """ 
To record your finances:    

1. Press the button for the category 
2. Reply with details of what you purchased (optional) 
3. Press "Cost 💵" and enter an amount
4. ...after a few iterations, click "summary"
"""

# Summary example used for testing.
SUMMARY = """
---------------
Example 
---------------
Month: July 2024

Groceries 🍅🥛: 20
Transport 🚙: 10
Clothes 👕: 100
"""

# These are the menu URBAN_LABELS used in the chatbot's UI.
FINANCE_LABELS = {
    "c1": "Groceries 🍅🥛",
    "c2": "Transport 🚙",
    "c3": "Clothes 👕",
    "c4": "House 🛖📱💡",
    "c5": "Fun 🏝️🍹🍰",
    "other": "Other..📃",
    "picture": "Picture 📃",
    "cost": "Cost 💵",
    "summary": "Summary",

    # The start message sent when the user hits the big red button to initiate a
    # first time chat with the chatbot.
    "start": "/start"
}

# Time management start message
TIME_MANAGEMENT_START_MSG = """ 
1. Press the button for the category 
2. Reply with details of what you did (optional) 
3. Press "Time 🕰️" and enter a duration 
4. ...after a few iterations, click "summary"
"""


# Labels used to manage the time management chatbot.
TIME_MANAGEMENT_LABELS = {
    "c1": "Creating 🥷",
    "c2": "Understanding 🕵️",
    "c3": "🔥 -fighting",
    "c4": "Writing 🖋️",
    "c5": "Recharging 🔋",
    "other": "Other..📃",
    "picture": "Picture 📃",
    "cost": "Time 🕰️",
    "summary": "Summary",

    # The start message sent when the user hits the big red button to initiate a
    # first time chat with the chatbot.
    "start": "/start"
}


# LABELS are the labels used in the chatbot's menu and buttons.
# TODO(prashanth@): configure this via flag.
LABELS = FINANCE_LABELS
START_MSG = FINANCE_START_MSG


# A test summary to capture in the summary pdf.
TEST_SUMMARY = '''
Summary from 10-1-2024 to 11-1-2024
Groceries: 20
Transport: 20
House: 100
Fun: 10
'''

# Used to timstamp updates.
INDIA_TZ = 'Asia/Kolkata'

# A pattern matching the first line of the summary in the symmary pdf.
SUMMARY_PATTERN = r"Summary from ([\d\-]+) to ([\d\-]+)"

# A pattern matching each line item (i.e each category) of the summary pdf.
CATEGORY_PATTERN = r"(\w+.*):\s*(\d+)"

# Base template file used to stylize the summary pdf.
TEMPLATE_PATH = "./template.pdf"

# The only characters allowed in the pdf summary.
ALLOWED_CHARS = r"[^a-zA-Z0-9\s\t\-_:\n.,;!?(){}\[\]'\"@#$%&*+=]"

# A placeholder for when the expense is unknown (i.e the user doesn't enter a
# desription).
UNKNOWN = "unknown"
