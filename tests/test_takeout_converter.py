from pathlib import Path

import pytest
from .fixtures import CSV_FILES, CSV_RECORDS

@pytest.fixture
def mock_csv_dir(mocker):
    mock_open = mocker.MagicMock()
    mock_open.return_value.__enter__.side_effect = CSV_FILES
    mocker.patch('play_takeout_to_plex.takeout_converter.open', mock_open)
    return mock_open


class TestFuseMainCsv:
    @pytest.fixture
    def target(self):
        from play_takeout_to_plex.takeout_converter import fuse_main_csv
        return fuse_main_csv

    def test_fuse_main_csv(self, mocker, mock_csv_dir, target):
        mock_path = mocker.Mock()
        mock_path.glob.return_value = [mock_path] * len(CSV_FILES)
        res = target(mock_path)
        assert res == CSV_RECORDS
