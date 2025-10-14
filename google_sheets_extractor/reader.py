import os
import pickle
import time
import hashlib
from googleapiclient.errors import HttpError

# --- CACHE CONFIGURATION ---
CACHE_DIR = "cache"
CACHE_DURATION = 3600  # Cache duration in seconds (1 hour)

def _get_cache_key(spreadsheet_id: str, sheet_titles: list) -> str:
    """Generates a unique cache key for a set of sheets."""
    # Sort titles to ensure cache key is consistent regardless of order
    sorted_titles = sorted(sheet_titles)
    key_string = f"{spreadsheet_id}_{'_'.join(sorted_titles)}"
    # Use a hash to keep the filename manageable
    return hashlib.md5(key_string.encode()).hexdigest() + ".pkl"

def _load_from_cache(cache_path: str) -> dict | None:
    """Loads data from a cache file if it's valid."""
    if os.path.exists(cache_path):
        # Check if the cache file is within the CACHE_DURATION
        file_mod_time = os.path.getmtime(cache_path)
        if (time.time() - file_mod_time) < CACHE_DURATION:
            print(f"Cache hit. Loading data from {cache_path}")
            with open(cache_path, "rb") as f:
                return pickle.load(f)
    print("Cache miss.")
    return None

def _save_to_cache(cache_path: str, data: dict):
    """Saves data to a cache file."""
    # Ensure the cache directory exists
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    print(f"Saving data to cache: {cache_path}")
    with open(cache_path, "wb") as f:
        pickle.dump(data, f)

def get_spreadsheet_metadata(service: object, spreadsheet_id: str) -> dict:
    """
    Retrieves metadata for all sheets in a spreadsheet.

    Args:
        service (object): The authorized Google Sheets API service object.
        spreadsheet_id (str): The ID of the Google Spreadsheet.

    Returns:
        dict: A dictionary containing the spreadsheet's metadata, focused on sheet properties.

    Raises:
        HttpError: If the API call fails.
    """
    try:
        # Use a field mask to retrieve only the sheet titles and IDs
        fields = 'sheets.properties.title,sheets.properties.sheetId'
        request = service.spreadsheets().get(spreadsheetId=spreadsheet_id, fields=fields)
        spreadsheet = request.execute()
        return spreadsheet
    except HttpError as e:
        print(f"An API error occurred while fetching spreadsheet metadata: {e}")
        raise

def get_sheet_values(service: object, spreadsheet_id: str, sheet_title: str) -> list:
    """
    Retrieves all values from a specific sheet within a spreadsheet.

    Args:
        service (object): The authorized Google Sheets API service object.
        spreadsheet_id (str): The ID of the Google Spreadsheet.
        sheet_title (str): The title of the sheet to read from (e.g., 'Sheet1').

    Returns:
        list: A list of lists containing the raw cell values from the sheet.

    Raises:
        HttpError: If the API call fails.
    """
    try:
        # Define a broad range to read all data from the sheet
        range_name = f"'{sheet_title}'!A:Z"

        request = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            majorDimension='ROWS',
            valueRenderOption='UNFORMATTED_VALUE',
            dateTimeRenderOption='SERIAL_NUMBER'
        )
        response = request.execute()
        return response.get('values', [])
    except HttpError as e:
        print(f"An API error occurred while fetching sheet values: {e}")
        raise

def get_multiple_sheet_values(service: object, spreadsheet_id: str, sheet_titles: list) -> dict:
    """
    Retrieves all values from multiple specific sheets within a spreadsheet using a batch request.
    It uses a local cache to avoid redundant API calls.

    Args:
        service (object): The authorized Google Sheets API service object.
        spreadsheet_id (str): The ID of the Google Spreadsheet.
        sheet_titles (list): A list of the titles of the sheets to read from.

    Returns:
        dict: A dictionary where keys are sheet titles and values are the raw cell values.

    Raises:
        HttpError: If the API call fails.
    """
    # --- CACHE LOGIC ---
    cache_key = _get_cache_key(spreadsheet_id, sheet_titles)
    cache_path = os.path.join(CACHE_DIR, cache_key)

    # Try loading from cache first
    cached_data = _load_from_cache(cache_path)
    if cached_data is not None:
        return cached_data

    # If cache miss, fetch from API
    print("Fetching data from Google Sheets API...")
    try:
        ranges = [f"'{title}'!A:Z" for title in sheet_titles]

        request = service.spreadsheets().values().batchGet(
            spreadsheetId=spreadsheet_id,
            ranges=ranges,
            majorDimension='ROWS',
            valueRenderOption='UNFORMATTED_VALUE',
            dateTimeRenderOption='SERIAL_NUMBER'
        )
        response = request.execute()

        # The response contains a list of 'valueRanges'. We need to map them back to sheet titles.
        results = {}
        for i, value_range in enumerate(response.get('valueRanges', [])):
            sheet_title = sheet_titles[i]
            results[sheet_title] = value_range.get('values', [])

        # Save the fresh data to cache
        _save_to_cache(cache_path, results)

        return results
    except HttpError as e:
        print(f"An API error occurred while fetching multiple sheet values: {e}")
        raise