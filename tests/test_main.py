from unittest.mock import patch, MagicMock, mock_open
import pytest
from google_sheets_extractor.main import main
import pandas as pd

@patch('google_sheets_extractor.main.authenticate_google_sheets')
@patch('google_sheets_extractor.main.get_multiple_sheet_values')
@patch('google_sheets_extractor.main.create_new_sheet')
@patch('google_sheets_extractor.main.get_sheet_id')
@patch('google_sheets_extractor.main.write_to_spreadsheet')
@patch('google_sheets_extractor.main.add_dashboard_enhancements')
@patch('os.path.exists', return_value=True)
@patch("builtins.open", new_callable=mock_open, read_data="""
metrics:
  total_pontos:
    column: pontos
    agg: sum
""")
def test_main_pipeline_dynamic_sheets(
    mock_open, mock_exists, mock_add_enhancements, mock_write, mock_get_id, mock_create_sheet,
    mock_get_values, mock_auth
):
    """
    Integration test for the main pipeline with dynamic source sheets.
    """
    # --- Mock Setup ---
    mock_service = MagicMock()
    mock_auth.return_value = mock_service
    mock_get_id.return_value = 12345

    # Mock the data returned from the sheets
    mock_get_values.return_value = {
        "Pontuação": [
            ['matricula', 'pontos', 'periodo'],
            ['101', 10, '202301']
        ],
        "Ocorrência": [
            ['matricula', 'evento', 'periodo'],
            ['101', 'A', '202301']
        ]
    }

    # --- Execute ---
    main(
        spreadsheet_id="fake_id",
        credentials_file="fake_creds.json",
        source_sheets=["Pontuação", "Ocorrência"]
    )

    # --- Assertions ---
    # Verify that the pipeline ran with the correct, dynamic sheets
    mock_get_values.assert_called_once_with(
        mock_service, "fake_id", ["Pontuação", "Ocorrência"]
    )
    # Verify that the final report is written
    mock_write.assert_called_once()
    # Verify that enhancements are added
    mock_add_enhancements.assert_called_once()