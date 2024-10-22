"""This library handles the creation of the summary reports. 

All summary reports are created through byte buffers.  
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


class Summary:
    """A helper class to manage the data for the summary."""

    def __init__(
            self,
            user_name: str,
            start_date: str,
            end_date: str,
            category_totals: dict,
            description_totals: str):
        self.user_name = user_name
        self.start_date = start_date
        self.end_date = end_date
        self.category_totals = category_totals
        self.description_totals = description_totals

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
        pdf.set_font("NotoSans", "B", size=12)
        pdf.set_fill_color(200, 220, 255)
        pdf.cell(95, 10, "Category", 1, 0, 'C', fill=True)
        pdf.cell(95, 10, "Total Amount", 1, 1, 'C', fill=True)

        # Rows
        pdf.set_font("NotoSans", "", size=12)
        fill = False
        for category, total in self.category_totals.items():
            if fill:
                pdf.set_fill_color(245, 245, 245)
            else:
                pdf.set_fill_color(255, 255, 255)
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
            pdf.set_font("NotoSans", "B", size=12)

            # Category Header
            pdf.cell(190, 10, _clean(category), 1, 1, 'C', fill=True)

            # Add descriptions and totals as a table
            pdf.set_font("NotoSans", "", size=12)
            pdf.set_fill_color(245, 245, 245)  # Set alternating row color
            fill = False  # Toggle for alternating row colors

            # Create a two-column table: Description and Total Amount
            for description, total in descriptions.items():
                pdf.set_fill_color(
                    245, 245, 245) if fill else pdf.set_fill_color(255, 255, 255)
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


def create_summary(updates: list[Update]) -> BytesIO:
    """Creates a temp pdf file with a summary of the given updates. 

    Args: 
        updates: usually telegram bot updates of a single user. 

    Returns: 
        BytesIO: A temp buffer with the file contents. 
    """
    summary = updates_to_summary(updates)

    # Open a PDF document and add fonts to it
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("NotoSans", "", "fonts/NotoSans-Regular.ttf", uni=True)
    pdf.add_font("NotoSans", "B", "fonts/NotoSans-Bold.ttf", uni=True)

    # Title formatting
    pdf.set_font("NotoSans", "B", size=16)
    pdf.cell(0, 10, summary.title(), ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("NotoSans", "", size=12)
    pdf.multi_cell(0, 10, summary.intro(), border=1, align='J', fill=False)

    pdf.set_font("NotoSans", "B", size=14)
    pdf.cell(0, 10, "Top-Level Breakdown", ln=True, align='C')
    pdf.ln(5)

    summary.format_category_totals(pdf)

    # Leave some space and add the description breakdown
    pdf.ln(10)
    pdf.set_font("NotoSans", "B", size=14)
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
    """Strip emojis and othe special characters out of the text.

    The font used may not handle emojis, so restrict summary to bare minimum.
    """
    return re.compile(ALLOWED_CHARS).sub("", text).strip().lower()


def _is_category(message_text: str) -> bool:
    """Returns true if the given string is a category for expense tracking."""
    mtl = message_text.lower()
    return (mtl != _get_label("cost") and
            mtl in [_get_label(k) for k in LABELS.keys()])


def _get_label(l: str) -> str:
    """A convenience function to retrieve the lowercase label."""
    # TODO(prashanth@): strip emojis?
    return LABELS[l].lower()


def _log_warning(user_id, user_name, timestamp, message):
    """Uses the logger for output a formatted warning string."""
    logging.warning(
        f"Warning for user {user_name} (ID: {user_id}) at {timestamp}: {message}")


def _sort_updates_by_date(updates):
    """Sorts the update list by the date field."""
    return sorted(updates, key=lambda u: u.message.date)


def _fmt_date(d: date) -> str:
    """Formmats the given string in DD-MM-YYYY format."""
    return d.strftime("%d-%m-%Y")
