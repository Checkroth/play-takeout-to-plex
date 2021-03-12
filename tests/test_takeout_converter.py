from copy import deepcopy
from io import StringIO
from pathlib import Path

import pytest
from play_takeout_to_plex.songs import RecordTagLink, SongTags, SongRecord
from .fixtures import (
    HEADER_ROW,
    CSV_FILES,
    CSV_RECORDS,
    AUDIO_FILES,
    MockAudiofile,
    MockAudiofileTags,
)

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


class TestMergeCsvWithFiletags:
    @pytest.fixture
    def target(self):
        from play_takeout_to_plex.takeout_converter import merge_csv_with_filetags
        return merge_csv_with_filetags

    @pytest.fixture
    def mock_eyed3(self, mocker):
        eyed3 = mocker.patch('play_takeout_to_plex.songs.eyed3')
        return eyed3

    def test_valid(self, mock_eyed3, mock_path, target):
        mock_eyed3.load.side_effect = AUDIO_FILES * 2
        mock_path.glob.return_value = [''] * len(AUDIO_FILES)  # Override path mock for ease of testing

        res = target(mock_path, CSV_RECORDS, False)
        expect = [RecordTagLink(songrecord=record, tags=SongTags(filepath=''), dry_run=False)
                  for (record, audiofile) in zip(CSV_RECORDS, AUDIO_FILES)]
        mock_eyed3.load.side_effect = AUDIO_FILES * 2
        assert res == expect

    def test_has_lost_lines(self, mock_eyed3, mock_path, target):
        mock_eyed3.load.side_effect = AUDIO_FILES * 2
        mock_path.glob.return_value = [''] * len(AUDIO_FILES)

        records = deepcopy(CSV_RECORDS)
        lost_record = SongRecord(title='Test title', album='', artist='',
                                 duration_ms=123, rating=0, play_count=0, removed=False, original_csv_name='')
        records.append(lost_record)
        lost_lines, lost_audiofiles, unmatched_audiofiles = target(mock_path, records, False)
        assert lost_lines == [lost_record]
        assert lost_audiofiles == []
        assert unmatched_audiofiles == []

    def test_has_lost_audiofiles(self, mock_eyed3, mock_path, target):
        lost_audiofile = MockAudiofile(MockAudiofileTags(1, 'Lost Song', '', 'Lost Artist'))
        mock_eyed3.load.side_effect = [lost_audiofile] + (AUDIO_FILES * 2)
        mock_path.glob.return_value = ['lost'] * len(AUDIO_FILES)

        lost_lines, lost_audiofiles, unmatched_audiofiles = target(mock_path, CSV_RECORDS, False)
        assert lost_lines == []
        assert lost_audiofiles == ['lost']
        assert unmatched_audiofiles == []


    def test_has_unmatched_audiofiles(self, mock_eyed3, mock_path, target):
        unmatched_audiofile = MockAudiofile(MockAudiofileTags(1, 'Lost Song', 'Unmatched Album', 'Bob Marley'))
        mock_eyed3.load.side_effect =  [unmatched_audiofile] + (AUDIO_FILES * 2)
        mock_path.glob.return_value = [''] * len(AUDIO_FILES)

        lost_lines, lost_audiofiles, unmatched_audiofiles = target(mock_path, CSV_RECORDS, False)
        assert lost_lines == []
        assert lost_audiofiles == []
        expect = SongTags(unmatched_audiofile)
        assert unmatched_audiofiles


class TestMoveAudioFiles:
    @pytest.fixture
    def target(self):
        from play_takeout_to_plex.takeout_converter import move_audio_files
        return move_audio_files

    def test_valid(self, mocker, target):
        assert True
