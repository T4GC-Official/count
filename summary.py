"""This library handles the creation of the summary reports. 

All summary reports are created through byte buffers.  

@TODO(prashanth@): This file needs a refactor. Summary and create_summary are 
common classes, but currently only the OM chatot converts updates to summary, 
and only the Lipok chatbot converts metadata to summary. 

@TODO(prashanth@): Add support for Devanagari. The fpdf library has RTL issues
supporting Gargi font and NotoDevanagari doesn't work with fpdf. We need to use
reportlab to support Devanagari.
"""
from fpdf import FPDF
from typing import Any, Dict
from constants import LABELS, TEST_SUMMARY, SUMMARY_PATTERN, CATEGORY_PATTERN, TEMPLATE_PATH, ALLOWED_CHARS, UNKNOWN
import PyPDF2
from pdfrw import PdfReader, PdfWriter, PageMerge
import re
import logging
from collections import defaultdict
from typing import List, Dict, Any
from datetime import datetime, date
from io import BytesIO
from telegram import Update
from translations.lipok import get_button_text, LANGUAGE


class Summary:
    """A helper class to manage the data for the summary."""

    def __init__(
            self,
            user_name: str,
            start_date: str,
            end_date: str,
            category_totals: dict,
            description_totals: str,
            language: str = "en"):
        self.user_name = user_name
        self.start_date = start_date
        self.end_date = end_date
        self.category_totals = category_totals
        self.description_totals = description_totals
        if language != "en":
            logging.info(f"Setting font family to: {language}")
            # TODO(prashanth@): NotoSansDevanagari does NOT work. Emperically
            # tested.
            self.font_family = "Gargi"
        else:
            logging.info(f"Setting font family to: {language}")
            self.font_family = "NotoSans"

    def title(self):
        return f"Summary from {self.start_date} to {self.end_date}"

    def intro(self):
        return f"Welcome {self.user_name}. Please find your summaries below."

    @staticmethod
    def get_title_pattern():
        return r"Summary from (\d{1,2}-\d{1,2}-\d{4}) to (\d{1,2}-\d{1,2}-\d{4})"

    @staticmethod
    def get_category_pattern():
        """Returns a regex to match the new category totals format.

        Eg: "Category    100"
        - (.*?): Matches the category name lazily (captures until whitespace)
        - \s+: Matches one or more spaces (used as separator in table)
        - (\d+): Captures the total amount as a group of digits
        """
        return r"(.*?)\s+(\d+)"

    def format_category_totals(self, pdf):
        """Create a table layout for category totals in the PDF."""

        # Header
        pdf.set_font(self.font_family, "B", size=12)

        pdf.set_fill_color(200, 220, 255)
        pdf.cell(95, 10, "Category", 1, 0, 'C', fill=True)
        pdf.cell(95, 10, "Total Amount", 1, 1, 'C', fill=True)

        # Rows
        pdf.set_font(self.font_family, "", size=12)
        fill = False
        for category, total in self.category_totals.items():
            if fill:
                pdf.set_fill_color(245, 245, 245)
            else:
                pdf.set_fill_color(255, 255, 255)
            logging.info(f"Inserting Category: {_clean(category)}: {total}")
            pdf.cell(95, 10, _clean(category), 1, 0, 'C', fill=True)
            pdf.cell(95, 10, str(total), 1, 1, 'C', fill=True)
            fill = not fill

    def format_description_totals(self, pdf):
        """Formats the description based summary into a table."""

        # Create table headers and alternate row styling for descriptions

        # Iterate through each category and its descriptions
        for category, descriptions in self.description_totals.items():
            # Light blue for category headers
            pdf.set_fill_color(220, 240, 255)
            pdf.set_font(self.font_family, "B", size=12)

            # Category Header
            pdf.cell(190, 10, _clean(category), 1, 1, 'C', fill=True)

            # Add descriptions and totals as a table
            pdf.set_font(self.font_family, "", size=12)
            pdf.set_fill_color(245, 245, 245)  # Set alternating row color
            fill = False  # Toggle for alternating row colors

            # Create a two-column table: Description and Total Amount
            for description, total in descriptions.items():
                pdf.set_fill_color(
                    245, 245, 245) if fill else pdf.set_fill_color(255, 255, 255)
                logging.info(
                    f"Inserting Description: {_clean(description)}: {total}")
                pdf.cell(95, 10, _clean(description), 1, 0, 'C', fill=True)
                pdf.cell(95, 10, str(total), 1, 1, 'C', fill=True)
                fill = not fill

            # Leave some space between categories
            pdf.ln(5)

    @staticmethod
    def to_json(pdf_data: BytesIO) -> dict:
        """Returns the contents of a summary pdf/text as json. 

        As method is heavily dependent on the way createSummary works, it is only used in testing. 

        Arguments:
            pdf_data: bytes of the summary pdf.

        Returns: 
            A dict with the contents of the summary document. Eg: 
            {
                "category": "net amount",
                .. for each category in the pdf ..
                "date": {
                    "start": report start date,
                    "end": report end date, 
                }
            }

        Raises:
            ValueError: if the date or category regexes don't match any content.
        """
        reader = PyPDF2.PdfReader(pdf_data)
        text = ""
        for page in reader.pages:
            text += page.extract_text()

        return Summary._parse(text)

    @staticmethod
    def _parse(text: str) -> dict:
        """Json-ifies the given summary text."""
        date_pattern = re.search(Summary.get_title_pattern(), text)
        if date_pattern is None:
            raise ValueError('Summary pdf does not contain date pattern.')

        start_date, end_date = date_pattern.groups()

        category_pattern = re.compile(
            Summary.get_category_pattern()).findall(text)
        if not category_pattern:
            raise ValueError('Summary pdf does not contain categories.')

        result = {}
        for category, value in category_pattern:
            for k, v in LABELS.items():
                # The unittest will check for the labels but the summary
                # is stripped of special characters. So replace the
                # stripped characters with the emoji labels.
                if _clean(category) in _clean(v):
                    result[v] = int(value)
                    break
        result['date'] = {
            'start': start_date,
            'end': end_date,
        }
        return result


def updates_to_summary(updates: List[Update]) -> Summary:
    """Generates a summary object describing the given list of updates.

    Arguments:
        updates: a list of telegram.ext update objects retrieved from the db.

    Return: 
        str: summary string 
    """
    updates = _sort_updates_by_date(updates)

    # category_totals eg:
    # {"Groceries": 100, "Transport": 10...}
    category_totals = defaultdict(int)

    # description_totals eg:
    # {"Groceries": {"rice": 100, "channa": 20}, "Transport": {"auto": 100}}
    description_totals = defaultdict(lambda: defaultdict(int))

    current_category = ""
    current_description = UNKNOWN

    for update in updates:
        message_text = update.message.text.strip().lower()
        if (message_text == _get_label("start") or
                message_text == _get_label("summary")):
            continue

        # Every digit is accumulated in the last (category, desc).
        if _is_category(message_text):
            current_category = message_text
            current_description = UNKNOWN
        elif message_text.isdigit():
            cost = int(message_text)
            category_totals[current_category] += cost
            description_totals[
                current_category][current_description] += cost
        else:
            if message_text != _get_label("cost"):
                current_description = message_text

    return Summary(
        updates[0].message.from_user.name,
        _fmt_date(updates[0].message.date),
        _fmt_date(updates[-1].message.date),
        category_totals,
        description_totals)


def metadata_to_summary(metadata: list[dict]) -> Summary:
    """Creates a summary object from the given metadata.

    Args:
        metadata: a list of dicts with the metadata. Eg:
        [
            {
                _id: ObjectId('6789232cd6414d468489548c'),
                update_id: 308371405,
                selection_path: '7196436554:/
                start:food:wheat:outside:custom:10',
                timestamp: ISODate('2025-01-16T15:18:04.490Z'),
                user_id: Long('7196436554'),
                user_name: 'redpig',
                user_username: null,
                user_language_code: 'en'
            },
            {
                _id: ObjectId('6789232cd6414d468489548e'),
                update_id: 308371405,
                selection_path: '7196436554:/start',
                timestamp: ISODate('2025-01-16T15:18:04.869Z'),
                user_id: Long('7196436554'),
                user_name: 'redpig',
                user_username: null,
                user_language_code: 'en'
            }
        ]

    Returns:
        Summary: a summary object. The fields of the summary are set as
        follows:
        - user_name: the user name from the first metadata entry.
        - start_date: the timestamp of the earliest metadata entry.
        - end_date: the timestamp of the latest metadata entry.
        - category_totals: a dict with the category totals, eg:
            {"food": 100, "fuel": 200}
        - description_totals: a dict with the description totals, eg:
            {"food": {"wheat": 100, "rice": 200}}

    Essentially the selection path is processed as follows:
    - The selection path is split by the colon (:) character.
    - The last element in this list is then split on the dash (-) character.
    - If the last element in this list is a digit, the metadata is processed as
      follows:
        * The first element is the user id. This is ignored.
        * The second element is /start. This is ignored.
        * The third element is the category. Eg: food.
        * The fourth element is the description. Eg: wheat.
        * N elements after the fourth (eg: outside, custom) are ignored.
        * The last element is the cost.
        * If there is a "-" in the last element, the upper number is used as
          the cost, else the only element is used (since it was a custom cost).
        * These costs are accumulated in the category_totals and
          description_totals.
    - If after splitting on "-" the last element is not a digit, the entire
      metadata is ignored.
    """
    # Initialize tracking dictionaries
    category_totals = defaultdict(int)
    description_totals = defaultdict(lambda: defaultdict(int))

    # Sort metadata by timestamp to get correct start/end dates
    sorted_metadata = sorted(metadata, key=lambda x: x['timestamp'])

    if not sorted_metadata:
        raise ValueError("Empty metadata list provided")

    # Get user info and dates from first/last entries
    user_name = sorted_metadata[0]['user_name']
    start_date = _fmt_date(sorted_metadata[0]['timestamp'])
    end_date = _fmt_date(sorted_metadata[-1]['timestamp'])

    for entry in sorted_metadata:
        path_elements = entry['selection_path'].split(':')

        # Skip if not enough elements for a valid cost entry.
        # We need at least userid, /start, category, description, cost.
        if len(path_elements) < 5:
            continue

        # Get the last element (potential cost)
        last_element = path_elements[-1]

        # Check if it contains a cost
        # In both ValueError cases we conclude that the last element is not a
        # cost and ignore this metadata entry.
        cost = None
        if '-' in last_element:
            # Take the higher number for range selections
            try:
                cost = max(int(x) for x in last_element.split('-'))
            except ValueError:

                continue
        else:
            try:
                cost = int(last_element)
            except ValueError:
                continue

        # With a valid cost entry, we can work backwards:
        #   * Category is the third element (index 2)
        #   * "Description" is the fourth element (index 3)
        #       - Description is overloaded here. It can be a custom description
        #         (entered by the user - like with OM) or a category button
        #         pressed by the user (like with Lipok).
        #   * The rest of the elements are ignored.
        category = path_elements[2]
        description = path_elements[3]

        # Update totals
        category_totals[category] += cost
        description_totals[category][description] += cost

    logging.info(f"Category Totals: {category_totals}")
    logging.info(f"Description Totals: {description_totals}")

    # TODO(prashanth@): Add language to the summary instead of inlining it
    # here. Key off-of the language kwarg already given to set font-family.
    # It is done here currently just so we don't disrupt the OM flow.

    # TODO(prashanth@): Add support for Devanagari. The fpdf library has RTL
    # issues supporting Gargi font and NotoDevanagari doesn't work with fpdf.
    # We need to use reportlab to support Devanagari.
    return Summary(
        user_name=user_name,
        start_date=start_date,
        end_date=end_date,
        category_totals={
            get_button_text(k, language="en"): v
            for k, v in category_totals.items()
        },
        description_totals={
            get_button_text(k, language="en"): {
                get_button_text(d, language="en"): v
                for d, v in v.items()
            }
            for k, v in description_totals.items()
        },
        language="en"
    )


def create_summary(updates: list[Update], metadata: list[dict]) -> BytesIO:
    """Creates a temp pdf file with a summary of the given updates. 

    Args: 
        updates: usually telegram bot updates of a single user. 

    Returns: 
        BytesIO: A temp buffer with the file contents. 
    """
    if updates and not metadata:
        summary = updates_to_summary(updates)
    elif metadata and not updates:
        summary = metadata_to_summary(metadata)
    elif updates and metadata:
        raise ValueError(
            "Both updates and metadata provided. Only one is allowed.")
    else:
        logging.error("No updates or metadata provided")
        return None

    # Open a PDF document and add fonts to it
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("NotoSans", "", "fonts/NotoSans-Regular.ttf", uni=True)
    pdf.add_font("NotoSans", "B", "fonts/NotoSans-Bold.ttf", uni=True)
    pdf.add_font("Gargi", "", "fonts/Gargi.ttf", uni=True)
    pdf.add_font("Gargi", "B", "fonts/Gargi.ttf", uni=True)

    # Title formatting
    pdf.set_font(summary.font_family, "B", size=16)
    pdf.cell(0, 10, summary.title(), ln=True, align='C')
    pdf.ln(10)

    pdf.set_font(summary.font_family, "", size=12)
    pdf.multi_cell(0, 10, summary.intro(), border=1, align='J', fill=False)

    pdf.set_font(summary.font_family, "B", size=14)
    pdf.cell(0, 10, "Top-Level Breakdown", ln=True, align='C')
    pdf.ln(5)

    summary.format_category_totals(pdf)

    # Leave some space and add the description breakdown
    pdf.ln(10)
    pdf.set_font(summary.font_family, "B", size=14)
    pdf.cell(0, 10, "Detailed Breakdown by Category", align='C', ln=True)
    pdf.ln(5)

    summary.format_description_totals(pdf)

    # Write to Bytes buffer and merge with template
    pdf_string = pdf.output(dest='S').encode('latin1')
    summary_pdf_buffer = BytesIO(pdf_string)

    return merge(summary_pdf_buffer, TEMPLATE_PATH)


def merge(
        summary_pdf_buffer: BytesIO, template_pdf_path: str) -> BytesIO:
    """Merge the given pdf with the given template.

    Arguments:
        summary_pdf_path: path to the pdf containig the summary string. 
        template_pdf_path: the summary is written over this template. 

    Return: 
        BytesIO: A temp bytes buffer with the merged file contents.  
    """
    merged_pdf_buffer = BytesIO()

    # Read the template and the summary PDF
    template_pdf = PdfReader(template_pdf_path)
    summary_pdf = PdfReader(summary_pdf_buffer)
    output_pdf = PdfWriter()

    # Merge all pages in the summary into the template.
    template_page = template_pdf.pages[0]
    for summary_page in summary_pdf.pages:
        template_clone = PageMerge().add(template_page).render()
        merger = PageMerge(template_clone)
        merger.add(summary_page, prepend=False).render()
        output_pdf.addpage(template_clone)

    # Write the merged content to the temporary buffer.
    output_pdf.write(merged_pdf_buffer)
    merged_pdf_buffer.seek(0)

    return merged_pdf_buffer


def _clean(text: str) -> str:
    """Strip emojis and special characters while preserving non-English scripts.

    The font used may not handle emojis, so restrict those, but keep 
    non-English characters like Devanagari (Hindi), Chinese, etc.

    Args:
        text: Input text that may contain emojis, special chars and non-English 
        scripts

    Returns:
        Cleaned text with emojis/special chars removed but scripts preserved
    """
    logging.debug(f"Pre Cleaning text: {text}")
    # First remove emojis using a more specific pattern
    emoji_pattern = re.compile("["
                               # emoticons
                               u"\U0001F600-\U0001F64F"
                               # symbols & pictographs
                               u"\U0001F300-\U0001F5FF"
                               # transport & map symbols
                               u"\U0001F680-\U0001F6FF"
                               # flags (iOS)
                               u"\U0001F1E0-\U0001F1FF"
                               u"\U00002702-\U000027B0"
                               u"\U000024C2-\U0001F251"
                               "]+", flags=re.UNICODE)

    # Remove emojis first
    text = emoji_pattern.sub('', text)

    # Remove other special characters while preserving letters/numbers from any
    # script
    cleaned = re.sub(r'[^\w\s\u0900-\u097F]', '', text)

    logging.debug(f"Post Cleaning text: {cleaned}")
    return cleaned.strip().lower()


def _is_category(message_text: str) -> bool:
    """Returns true if the given string is a category for expense tracking."""
    mtl = message_text.lower()
    return (mtl != _get_label("cost") and
            mtl in [_get_label(k) for k in LABELS.keys()])


def _get_label(l: str) -> str:
    """A convenience function to retrieve the lowercase label."""
    # TODO(prashanth@): strip emojis?
    return LABELS[l].lower()


def _sort_updates_by_date(updates):
    """Sorts the update list by the date field."""
    return sorted(updates, key=lambda u: u.message.date)


def _fmt_date(d: date) -> str:
    """Formmats the given string in DD-MM-YYYY format."""
    return d.strftime("%d-%m-%Y")
