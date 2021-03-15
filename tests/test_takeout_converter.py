from unittest.mock import call
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
    AUDIO_TAGS,
    RECORD_LINKS,
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
        unmatched_audiofile = MockAudiofile(
            MockAudiofileTags(1, 'Lost Song', 'Unmatched Album', 'Bob Marley'))
        mock_eyed3.load.side_effect = [unmatched_audiofile] + (AUDIO_FILES * 2)
        mock_path.glob.return_value = [''] * len(AUDIO_FILES)

        lost_lines, lost_audiofiles, unmatched_audiofiles = target(mock_path, CSV_RECORDS, False)
        assert lost_lines == []
        assert lost_audiofiles == []
        assert unmatched_audiofiles


class TestMoveAudioFiles:
    @pytest.fixture
    def target(self):
        from play_takeout_to_plex.takeout_converter import move_audio_files
        return move_audio_files

    @pytest.fixture
    def mock_shutil(self, mocker):
        return mocker.patch('play_takeout_to_plex.takeout_converter.shutil')

    @pytest.fixture
    def expect_out_filenames(self):
        outpath = Path('testpath')
        return [
            outpath / 'Bob Marley/Live From London/03 - I Shot The Sheriff.mp3',
            outpath / 'Bob Marley/Burnin\'/05 - I Shot The Sheriff.mp3',
            outpath / 'Bob Marley/Live at Rockpalast/05 - I Shot The Sheriff.mp3',
            outpath / 'Bob Marley/Live!/06 - I Shot The Sheriff.mp3',
            outpath / 'Bob Marley/Live at the Lyceum/06 - I Shot The Sheriff.mp3',
            outpath / 'Bob Marley/Legend/07 - I Shot The Sheriff.mp3',
            outpath / 'OK Go/OK Go/09 - C-C-C-Cinnamon Lips.mp3',
            outpath / 'Weird Al Yankovic/Poodle Hat/01 - Couch Potato.mp3',
            outpath / 'Porcupine Tree/Deadwing/07 - Open Car.mp3',
            outpath / 'Weird Al Yankovic/Straight Outta Lynwood/01 - White & Nerdy.mp3',
        ]

    @pytest.fixture
    def expect_in_filenames(self):
        return [
            tag.filepath
            for tag in AUDIO_TAGS
        ]

    @pytest.fixture
    def expect_calls(self, expect_in_filenames, expect_out_filenames):
        return [
            call(origin, target)
            for origin, target
            in zip(expect_in_filenames, expect_out_filenames)
        ]

    def test_move_valid(self, mock_shutil, expect_calls, target):
        outpath = Path('testpath')
        target(
            target_path=outpath,
            tagged_data=RECORD_LINKS,
            copy=False,
            dry_run=False,
        )
        assert mock_shutil.move.mock_calls == expect_calls
        mock_shutil.copy.assert_not_called()

    def test_copy_valid(self, mock_shutil, expect_calls, target):
        outpath = Path('testpath')
        target(
            target_path=outpath,
            tagged_data=RECORD_LINKS,
            copy=True,
            dry_run=False,
        )
        assert mock_shutil.copyfile.mock_calls == expect_calls
        mock_shutil.move.assert_not_called()

    @pytest.mark.parametrize('copy', [True, False])
    def test_dry_run_valid(self, mock_shutil, expect_calls, copy, target):
        outpath = Path('testpath')
        target(
            target_path=outpath,
            tagged_data=RECORD_LINKS,
            copy=copy,
            dry_run=True,
        )

        mock_shutil.move.assert_not_called()
        mock_shutil.copyfile.assert_not_called()

    # @pytest.mark.parametrize('copy', [True, False])
    def test_duplicate_origins_fails(self, mock_shutil, target):
        outpath = Path('testpath')
        duplicate_data = RECORD_LINKS[0]
        duplicate_data.title = 'new title!'
        data = RECORD_LINKS + [duplicate_data]
        with pytest.raises(ValueError):
            target(
                target_path=outpath,
                tagged_data=data,
                copy=False,
                dry_run=False,
            )

        mock_shutil.move.assert_not_called()
        mock_shutil.copyfile.assert_not_called()

    def test_duplicate_targets_fails(self):
        pass
