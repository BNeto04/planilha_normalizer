from datetime import datetime
from google_sheets_extractor.transformer import _convert_serial_to_datetime

def test_convert_serial_to_datetime():
    # Test case 1: A known date
    assert _convert_serial_to_datetime(43831) == datetime(2020, 1, 1)

    # Test case 2: A date with time
    assert _convert_serial_to_datetime(43831.5) == datetime(2020, 1, 1, 12, 0)

    # Test case 3: The epoch start date
    assert _convert_serial_to_datetime(0) == datetime(1899, 12, 30)

    # Test case 4: A more recent date
    assert _convert_serial_to_datetime(45631.75) == datetime(2024, 12, 5, 18, 0)