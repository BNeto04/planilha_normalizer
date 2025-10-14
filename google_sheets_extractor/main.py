import sys
import os
from dotenv import load_dotenv
from google_sheets_extractor.auth import authenticate_google_sheets
from google_sheets_extractor.reader import get_multiple_sheet_values
from google_sheets_extractor.transformer import normalize_data
from google_sheets_extractor.processor import reconcile_and_calculate
from google_sheets_extractor.writer import create_new_sheet, write_to_spreadsheet

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION ---
# Load from environment variables
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE")
# The new sheet where the report will be saved
OUTPUT_SHEET_TITLE = "RelatorioFinal"
# The source sheets to be processed
SOURCE_SHEETS = ["Pontuação", "Ocorrência", "Armas"]

def main():
    """
    Main orchestrator to extract, transform, process, and save data from Google Sheets.
    """
    print("Starting Google Sheets data processing pipeline...")

    # 1. Authentication
    try:
        if not CREDENTIALS_FILE or not os.path.exists(CREDENTIALS_FILE):
            print(f"Error: Credentials file not found at '{CREDENTIALS_FILE}'.")
            print("Please ensure the CREDENTIALS_FILE environment variable is set correctly.")
            sys.exit(1)

        if not SPREADSHEET_ID:
            print("Error: SPREADSHEET_ID environment variable not set.")
            sys.exit(1)

        service = authenticate_google_sheets(CREDENTIALS_FILE)
        print("Authentication successful.")
    except Exception as e:
        print(f"Authentication failed: {e}")
        sys.exit(1)

    # 2. Read Data from Multiple Sheets
    try:
        print(f"Reading data from sheets: {', '.join(SOURCE_SHEETS)}")
        raw_data_map = get_multiple_sheet_values(service, SPREADSHEET_ID, SOURCE_SHEETS)
    except Exception as e:
        print(f"Failed to read data from sheets: {e}")
        sys.exit(1)

    # 3. Normalize Data
    normalized_data_map = {}
    for sheet_title, raw_values in raw_data_map.items():
        if raw_values:
            normalized_data_map[sheet_title] = normalize_data(raw_values)
            print(f"Normalized data for sheet: '{sheet_title}'.")
        else:
            print(f"No data found in sheet: '{sheet_title}'.")

    # 4. Process and Calculate Metrics
    try:
        print("Reconciling data and calculating metrics...")
        metrics_df = reconcile_and_calculate(normalized_data_map)
        if metrics_df.empty:
            print("No metrics were generated. Exiting.")
            sys.exit(0)
        print("Metrics calculated successfully.")
        print("First 5 rows of the final report:")
        print(metrics_df.head())
    except Exception as e:
        print(f"An error occurred during data processing: {e}")
        sys.exit(1)

    # 5. Write Report to a New Sheet
    try:
        print(f"Preparing to write report to sheet: '{OUTPUT_SHEET_TITLE}'")
        # Ensure the output sheet exists
        create_new_sheet(service, SPREADSHEET_ID, OUTPUT_SHEET_TITLE)
        # Write the DataFrame to the sheet
        write_to_spreadsheet(service, SPREADSHEET_ID, OUTPUT_SHEET_TITLE, metrics_df)
        print("Report successfully written to Google Sheets.")
    except Exception as e:
        print(f"Failed to write the report to Google Sheets: {e}")
        sys.exit(1)

    print("\nProcessing pipeline finished successfully.")

if __name__ == "__main__":
    main()