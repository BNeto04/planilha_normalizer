import sys
import os
from google_sheets_extractor.auth import authenticate_google_sheets
from google_sheets_extractor.reader import get_spreadsheet_metadata, get_sheet_values
from google_sheets_extractor.transformer import normalize_data, generate_semantic_json

# --- CONFIGURATION ---
# IMPORTANT: Replace with your actual Spreadsheet ID and credentials file path.
SPREADSHEET_ID = "YOUR_SPREADSHEET_ID_HERE"
CREDENTIALS_FILE = "path/to/your/credentials.json"
# Optional: Specify a single sheet to process. If None, all sheets will be processed.
# TARGET_SHEET_TITLE = "Sheet1"
TARGET_SHEET_TITLE = None

def main():
    """
    Main orchestrator to extract, transform, and save data from Google Sheets.
    """
    print("Starting Google Sheets data extraction process...")

    # 1. Authentication
    try:
        if not os.path.exists(CREDENTIALS_FILE):
            print(f"Error: Credentials file not found at '{CREDENTIALS_FILE}'.")
            print("Please update the CREDENTIALS_FILE variable in main.py.")
            sys.exit(1)

        if SPREADSHEET_ID == "YOUR_SPREADSHEET_ID_HERE":
            print("Error: Please replace 'YOUR_SPREADSHEET_ID_HERE' with your actual Spreadsheet ID.")
            sys.exit(1)

        service = authenticate_google_sheets(CREDENTIALS_FILE)
        print("Authentication successful.")
    except Exception as e:
        print(f"Authentication failed: {e}")
        sys.exit(1)

    # 2. Get Sheet Metadata
    try:
        metadata = get_spreadsheet_metadata(service, SPREADSHEET_ID)
        sheets = metadata.get('sheets', [])
        if not sheets:
            print("No sheets found in the spreadsheet.")
            sys.exit(0)

        print(f"Found {len(sheets)} sheet(s) in the spreadsheet.")
    except Exception as e:
        print(f"Failed to retrieve spreadsheet metadata: {e}")
        sys.exit(1)

    # 3. Process each sheet
    all_results = []
    for sheet in sheets:
        sheet_title = sheet.get('properties', {}).get('title')
        if not sheet_title:
            continue

        if TARGET_SHEET_TITLE and sheet_title != TARGET_SHEET_TITLE:
            print(f"Skipping sheet: '{sheet_title}' (not the target).")
            continue

        print(f"Processing sheet: '{sheet_title}'...")

        try:
            # 4. Read Data
            raw_values = get_sheet_values(service, SPREADSHEET_ID, sheet_title)
            if not raw_values:
                print(f"No data found in sheet: '{sheet_title}'. Skipping.")
                continue

            # 5. Normalize Data
            normalized_records = normalize_data(raw_values)

            # 6. Generate JSON
            json_output = generate_semantic_json(normalized_records, SPREADSHEET_ID, sheet_title)

            # Save the output to a file
            output_filename = f"output_{sheet_title}.json"
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write(json_output)

            print(f"Successfully processed and saved data for '{sheet_title}' to '{output_filename}'.")
            all_results.append(json_output)

        except Exception as e:
            print(f"An error occurred while processing sheet '{sheet_title}': {e}")

    print("\nProcess finished.")
    if not all_results:
        print("No data was processed.")

if __name__ == "__main__":
    main()