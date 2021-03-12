from io import StringIO
from pathlib import Path

import pytest
from .fixtures import HEADER_ROW, CSV_FILES, CSV_RECORDS

@pytest.fixture
def mock_csv_dir(mocker):
    def with_context(side_effect):
        mock_open = mocker.MagicMock()
        mock_open.return_value.__enter__.side_effect = side_effect
        mocker.patch('play_takeout_to_plex.takeout_converter.open', mock_open)
        return mock_open

    return with_context


@pytest.fixture
def mock_path(mocker):
    mock = mocker.Mock()
    mock.name = ''
    mock.glob.return_value = [mock] * len(CSV_FILES)
    return mock


@pytest.fixture
def mock_logger(mocker):
    return mocker.patch('play_takeout_to_plex.takeout_converter.logger')


class TestFuseMainCsv:
    @pytest.fixture
    def target(self):
        from play_takeout_to_plex.takeout_converter import fuse_main_csv
        return fuse_main_csv

    def test_fuse_main_csv_valid(self, mock_path, mock_csv_dir, target):
        mock_csv_dir(CSV_FILES)
        res = target(mock_path)
        assert res == CSV_RECORDS

    def test_fuse_main_csv_no_header(self, mock_path, mock_csv_dir, mock_logger, target):
        mock_csv_dir([StringIO('')])
        res = target(mock_path)
        assert res is None
        mock_logger.error.assert_called_with('All csv files must begin with header')

    def test_fuse_main_csv_invalid_format(self, mock_path, mock_csv_dir, mock_logger, target):
        mock_csv_dir([StringIO(HEADER_ROW + str(CSV_RECORDS[0]) + 'extra,columns.raise,errors')])
        res = target(mock_path)
        assert res is None
        mock_logger.error.assert_called_with('CSV files are not in expected format.')


class TestOutputMainCsv:
    @pytest.fixture
    def target(self):
        from play_takeout_to_plex.takeout_converter import output_main_csv
        return output_main_csv

    def test_valid(self, mocker, mock_csv_dir, target):
        expect = HEADER_ROW + '\n'.join([str(record) for record in CSV_RECORDS])
        mock_file = mocker.Mock()
        file_handler = mock_csv_dir([mock_file])

        target(CSV_RECORDS, Path('testpath'))

        file_handler.assert_called_with(Path('testpath/main_csv.csv'), 'w')
        mock_file.writelines.assert_called_once_with(expect)
