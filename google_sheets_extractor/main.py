import sys
import os
from dotenv import load_dotenv
from google_sheets_extractor.auth import authenticate_google_sheets
from google_sheets_extractor.reader import get_multiple_sheet_values
from google_sheets_extractor.transformer import normalize_data
from google_sheets_extractor.schemas import validate_data
from google_sheets_extractor.processor import reconcile_and_calculate
from google_sheets_extractor.writer import (
    create_new_sheet,
    write_to_spreadsheet,
    get_sheet_id,
    add_dashboard_enhancements
)

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION ---
# The new sheet where the report will be saved
OUTPUT_SHEET_TITLE = "RelatorioFinal"
# Default source sheets if none are provided
DEFAULT_SOURCE_SHEETS = ["Pontuação", "Ocorrência", "Armas"]
# Path to the metrics configuration file
METRICS_CONFIG_FILE = "google_sheets_extractor/metrics.yaml"

def main(
    spreadsheet_id: str = None,
    credentials_file: str = None,
    source_sheets: list[str] = None
):
    """
    Main orchestrator to extract, transform, process, and save data from Google Sheets.

    Args:
        spreadsheet_id (str, optional): The ID of the Google Spreadsheet. Defaults to env var.
        credentials_file (str, optional): Path to credentials file. Defaults to env var.
        source_sheets (list[str], optional): A list of sheet titles to process. Defaults to DEFAULT_SOURCE_SHEETS.
    """
    print("Starting Google Sheets data processing pipeline...")

    # Determine credentials and spreadsheet ID to use
    creds_file = credentials_file or os.getenv("CREDENTIALS_FILE")
    sheet_id_to_process = spreadsheet_id or os.getenv("SPREADSHEET_ID")

    # 1. Authentication
    try:
        if not creds_file or not os.path.exists(creds_file):
            print(f"Error: Credentials file not found at '{creds_file}'.")
            print("Please ensure the CREDENTIALS_FILE environment variable is set or passed as an argument.")
            sys.exit(1)

        if not sheet_id_to_process:
            print("Error: SPREADSHEET_ID environment variable not set or passed as an argument.")
            sys.exit(1)

        service = authenticate_google_sheets(creds_file)
        print("Authentication successful.")
    except Exception as e:
        print(f"Authentication failed: {e}")
        sys.exit(1)

    # Determine which source sheets to use
    sheets_to_process = source_sheets or DEFAULT_SOURCE_SHEETS

    # 2. Read Data from Multiple Sheets
    try:
        print(f"Reading data from sheets: {', '.join(sheets_to_process)}")
        raw_data_map = get_multiple_sheet_values(service, sheet_id_to_process, sheets_to_process)
    except Exception as e:
        print(f"Failed to read data from sheets: {e}")
        sys.exit(1)

    # 3. Normalize and Validate Data
    normalized_data_map = {}
    for sheet_title, raw_values in raw_data_map.items():
        if raw_values:
            normalized_data = normalize_data(raw_values)
            print(f"Normalized data for sheet: '{sheet_title}'.")

            # Validate the normalized data against the schema
            validate_data(sheet_title, normalized_data)

            normalized_data_map[sheet_title] = normalized_data
        else:
            print(f"No data found in sheet: '{sheet_title}'.")

    # 4. Process and Calculate Metrics
    try:
        if not os.path.exists(METRICS_CONFIG_FILE):
            print(f"Error: Metrics configuration file not found at '{METRICS_CONFIG_FILE}'.")
            sys.exit(1)

        print("Reconciling data and calculating metrics...")
        metrics_df = reconcile_and_calculate(normalized_data_map, METRICS_CONFIG_FILE)
        if metrics_df.empty:
            print("No metrics were generated. Exiting.")
            sys.exit(0)
        print("Metrics calculated successfully.")
        print("First 5 rows of the final report:")
        print(metrics_df.head())
    except Exception as e:
        print(f"An error occurred during data processing: {e}")
        sys.exit(1)

    # 5. Write Report and Enhance Sheet
    try:
        print(f"Preparing to write report to sheet: '{OUTPUT_SHEET_TITLE}'")
        # Ensure the output sheet exists and get its ID
        create_new_sheet(service, sheet_id_to_process, OUTPUT_SHEET_TITLE)
        sheet_id = get_sheet_id(service, sheet_id_to_process, OUTPUT_SHEET_TITLE)

        # Write the DataFrame to the sheet
        write_to_spreadsheet(service, sheet_id_to_process, OUTPUT_SHEET_TITLE, metrics_df)
        print("Report data successfully written to Google Sheets.")

        # Add dashboard enhancements
        end_row, end_column = metrics_df.shape
        add_dashboard_enhancements(service, sheet_id_to_process, sheet_id, end_row + 1, end_column)

    except Exception as e:
        print(f"An error occurred during the write/enhancement process: {e}")
        sys.exit(1)

    print("\nProcessing pipeline finished successfully.")

if __name__ == "__main__":
    # When running as a script, it uses environment variables
    main()