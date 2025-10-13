import re
from datetime import datetime, timedelta
import json

def _convert_serial_to_datetime(serial_number: float) -> datetime:
    """
    Converts a Google Sheets serial number to a Python datetime object.
    Google Sheets uses 1899-12-30 as the base date (day 0).
    """
    # Google's epoch starts on 1899-12-30, which is equivalent to Python's datetime base + timedelta.
    # The integer part of the number is the number of days, the fractional part is the time.
    return datetime(1899, 12, 30) + timedelta(days=serial_number)

def _standardize_header(header: str) -> str:
    """
    Standardizes a string to be used as a JSON key.
    Converts to lowercase, replaces spaces and special characters with underscores.
    """
    s = header.lower()
    s = re.sub(r'\s+', '_', s)
    s = re.sub(r'[^a-z0-9_]', '', s)
    return s.strip('_')

def normalize_data(raw_values: list) -> list:
    """
    Normalizes raw data from a Google Sheet into a list of dictionaries.

    Args:
        raw_values (list): A list of lists representing rows from the sheet.

    Returns:
        list: A list of dictionaries, where each dictionary represents a structured row.
              Returns an empty list if raw_values is empty or has no data rows.
    """
    if not raw_values or len(raw_values) < 2:
        return []

    header_row = [_standardize_header(str(h)) for h in raw_values[0]]
    data_rows = raw_values[1:]

    normalized_records = []
    for row in data_rows:
        record = {}
        for i, value in enumerate(row):
            if i < len(header_row):
                header = header_row[i]
                # Check if the value is numeric (int or float) to identify potential date serials
                if isinstance(value, (int, float)):
                    # A simple heuristic: if a number is large, it could be a date.
                    # This could be refined with more context if needed.
                    # For now, we assume any numeric value could be a date to be converted.
                    try:
                        record[header] = _convert_serial_to_datetime(value)
                    except (ValueError, TypeError):
                        record[header] = value # Keep original if conversion fails
                else:
                    record[header] = value
        normalized_records.append(record)

    return normalized_records

def generate_semantic_json(normalized_data: list, spreadsheet_id: str, sheet_title: str) -> str:
    """
    Generates a final JSON output with metadata and structured data.

    Args:
        normalized_data (list): The list of normalized data records (dictionaries).
        spreadsheet_id (str): The ID of the source spreadsheet.
        sheet_title (str): The title of the source sheet.

    Returns:
        str: A JSON formatted string.
    """
    output = {
        "metadata": {
            "spreadsheetId": spreadsheet_id,
            "sheetTitle": sheet_title,
            "retrievalTimestamp": datetime.utcnow().isoformat() + "Z"
        },
        "data": normalized_data
    }
    return json.dumps(output, indent=4, default=str) # Use default=str to handle datetime objects