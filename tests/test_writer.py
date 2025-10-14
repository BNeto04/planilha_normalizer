import pytest
from unittest.mock import MagicMock, patch
from google_sheets_extractor.writer import write_to_spreadsheet, add_dashboard_enhancements

@pytest.fixture
def mock_service():
    """Fixture to create a mock Google Sheets API service object."""
    return MagicMock()

def test_write_to_spreadsheet_call(mock_service):
    """
    Smoke test to verify that write_to_spreadsheet calls the correct API method.
    """
    # Create a dummy DataFrame
    import pandas as pd
    df = pd.DataFrame({'col1': [1], 'col2': [2]})

    # Call the function
    write_to_spreadsheet(mock_service, 'test_id', 'test_sheet', df)

    # Assert that the update method was called
    mock_service.spreadsheets().values().update.assert_called_once()


def test_add_dashboard_enhancements_call(mock_service):
    """
    Smoke test to verify that add_dashboard_enhancements calls the batchUpdate method.
    """
    with patch.object(mock_service.spreadsheets(), 'batchUpdate') as mock_batch_update:
        # Call the function with dummy parameters
        add_dashboard_enhancements(mock_service, 'test_id', 123, 10, 5)

        # Assert that batchUpdate was called
        mock_batch_update.assert_called_once()