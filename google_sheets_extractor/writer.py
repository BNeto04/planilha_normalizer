from googleapiclient.errors import HttpError
from google_sheets_extractor.report_enhancements import (
    create_filter_view_request,
    create_chart_request,
    create_slicer_request,
    create_auto_resize_columns_request,
)

def create_new_sheet(service: object, spreadsheet_id: str, sheet_title: str):
    """
    Creates a new sheet in a spreadsheet if it doesn't already exist.

    Args:
        service (object): The authorized Google Sheets API service object.
        spreadsheet_id (str): The ID of the Google Spreadsheet.
        sheet_title (str): The title for the new sheet.
    """
    try:
        # Check if the sheet already exists
        spreadsheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = spreadsheet_metadata.get('sheets', '')
        for sheet in sheets:
            if sheet.get('properties', {}).get('title', '') == sheet_title:
                print(f"Sheet '{sheet_title}' already exists.")
                return

        # If not, create it
        body = {
            'requests': [{
                'addSheet': {
                    'properties': {
                        'title': sheet_title
                    }
                }
            }]
        }
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=body
        ).execute()
        print(f"Sheet '{sheet_title}' created successfully.")

    except HttpError as e:
        print(f"An API error occurred while creating the sheet: {e}")
        raise

def get_sheet_id(service: object, spreadsheet_id: str, sheet_title: str) -> int:
    """
    Retrieves the sheet ID for a given sheet title.

    Args:
        service: The authorized Google Sheets API service object.
        spreadsheet_id: The ID of the Google Spreadsheet.
        sheet_title: The title of the sheet.

    Returns:
        The sheet ID (integer).

    Raises:
        ValueError: If the sheet with the given title is not found.
    """
    try:
        spreadsheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = spreadsheet_metadata.get('sheets', [])
        for sheet in sheets:
            if sheet.get('properties', {}).get('title', '') == sheet_title:
                return sheet.get('properties', {}).get('sheetId')
        raise ValueError(f"Sheet with title '{sheet_title}' not found.")
    except HttpError as e:
        print(f"An API error occurred while retrieving the sheet ID: {e}")
        raise

def write_to_spreadsheet(service: object, spreadsheet_id: str, sheet_title: str, df_metrics):
    """
    Writes a DataFrame to a specified sheet in a Google Spreadsheet.

    Args:
        service (object): The authorized Google Sheets API service object.
        spreadsheet_id (str): The ID of the Google Spreadsheet.
        sheet_title (str): The title of the sheet to write to.
        df_metrics (pd.DataFrame): The DataFrame containing the metrics to write.
    """
    try:
        # Convert DataFrame to a list of lists for the API
        header = [list(df_metrics.columns)]
        values = df_metrics.values.tolist()
        data = header + values

        body = {
            'values': data
        }

        # The range where the data will be written. A1 notation.
        range_name = f"'{sheet_title}'!A1"

        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()

        print(f"{result.get('updatedCells')} cells updated in sheet '{sheet_title}'.")

    except HttpError as e:
        print(f"An API error occurred while writing to the spreadsheet: {e}")
        raise

def add_dashboard_enhancements(service: object, spreadsheet_id: str, sheet_id: int, end_row: int, end_column: int):
    """
    Adds interactive dashboard features to the specified sheet using a batchUpdate request.
    """
    print("Adding dashboard enhancements (filters, charts, slicers)...")

    requests = [
        create_filter_view_request(sheet_id, end_row, end_column),
        create_chart_request(sheet_id, end_row, end_column),
        create_slicer_request(sheet_id, end_row, end_column),
        create_auto_resize_columns_request(sheet_id, end_column),
    ]

    # Add Developer Metadata for each row
    for i in range(1, end_row):  # Skip header row
        requests.append({
            "createDeveloperMetadata": {
                "developerMetadata": {
                    "metadataKey": "origem_conciliacao",
                    "metadataValue": "v1.0",
                    "location": {
                        "dimensionRange": {
                            "sheetId": sheet_id,
                            "dimension": "ROWS",
                            "startIndex": i,
                            "endIndex": i + 1
                        }
                    },
                    "visibility": "PROJECT"
                }
            }
        })

    try:
        body = {"requests": requests}
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id, body=body
        ).execute()
        print("Dashboard enhancements added successfully.")
    except HttpError as e:
        print(f"An API error occurred while adding dashboard enhancements: {e}")
        raise