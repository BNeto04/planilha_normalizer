from googleapiclient.errors import HttpError

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

    Args:
        service (object): The authorized Google Sheets API service object.
        spreadsheet_id (str): The ID of the Google Spreadsheet.
        sheet_titles (list): A list of the titles of the sheets to read from.

    Returns:
        dict: A dictionary where keys are sheet titles and values are the raw cell values.

    Raises:
        HttpError: If the API call fails.
    """
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
            # Extract the sheet title from the range string used in the request
            sheet_title = sheet_titles[i]
            results[sheet_title] = value_range.get('values', [])

        return results
    except HttpError as e:
        print(f"An API error occurred while fetching multiple sheet values: {e}")
        raise