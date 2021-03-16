from pathlib import Path
import pytest

from .fixtures import MockAudiofile, MockAudiofileTags


class TestSongTags:
    @pytest.fixture
    def target(self):
        from play_takeout_to_plex.songs import SongTags
        return SongTags

    @pytest.mark.parametrize('titlenum,expect_track', [
        ('1', 1),
        ('5', 5),
        ('9', 9),
        ('01', 1),
        ('05', 5),
        ('09', 9),
        ('15', 15),
        ('41', 41),
        ('99', 99),
    ])
    def test_title_track_num_valid(self, mocker, titlenum, expect_track, target):
        mocktags = MockAudiofile(tag=MockAudiofileTags(
            track_num=9,
            title=f'{titlenum}  - Track Title',
            album='Test Album',
            artist='Test Artist',
        ))
        mocker.patch('play_takeout_to_plex.songs.eyed3.load', return_value=mocktags)
        assert target(filepath=Path('test')).title_track_num == expect_track

    @pytest.mark.parametrize('title', [
        'Title - With - Hyphens',
        'T1tl3 Has #s',
        'Regular Title!',
    ])
    def test_title_track_num_not_present(self, mocker, title, target):
        mocktags = MockAudiofile(tag=MockAudiofileTags(
            track_num=9,
            title=title,
            album='Test Album',
            artist='Test Artist',
        ))
        mocker.patch('play_takeout_to_plex.songs.eyed3.load', return_value=mocktags)
        assert target(filepath=Path('test')).title_track_num is None

    @pytest.mark.parametrize('title,expect', [
        ('Title.mp3', True),
        ('Title.literallyanything', True),
        ('Title Has . In its name', True),  # Would like to be false, but too annoying to implement
        ('Regular Title!', False),
    ])
    def test_has_title_extension_valid(self, mocker, title, expect, target):
        mocktags = MockAudiofile(tag=MockAudiofileTags(
            track_num=9,
            title=title,
            album='Test Album',
            artist='Test Artist',
        ))
        mocker.patch('play_takeout_to_plex.songs.eyed3.load', return_value=mocktags)
        assert target(filepath=Path('test')).has_title_extension is expect


class TestRecordTagLink:
    @pytest.fixture
    def target(self):
        from play_takeout_to_plex.songs import RecordTagLink
        return RecordTagLink

    @pytest.fixture
    def audiofile(self, mocker):
        mocktags = MockAudiofile(tag=MockAudiofileTags(
            track_num=7,
            title='07 - Open Car',
            album='Deadwing',
            artist='Porcupine Tree',
        ))
        mocker.patch('play_takeout_to_plex.songs.eyed3.load', return_value=mocktags)
        return mocktags

    @pytest.fixture
    def tags(self, audiofile, mocker):
        from play_takeout_to_plex.songs import SongTags
        return SongTags(filepath=Path('Google Play Music/Tracks/Porcupine Tree - Deadwing - Open Car.mp3'))

    @pytest.fixture
    def songrecord(self):
        from play_takeout_to_plex.songs import SongRecord
        return SongRecord(
            title='07 - Open Car',
            album='Deadwing',
            artist='Porcupine Tree',
            duration_ms=228414,
            rating=0,
            play_count=9,
            removed=False,
            original_csv_name='Google Play Music/Tracks/Open Car.csv',
        )

    @pytest.mark.parametrize('dry_run', [True, False])
    def test_init_sets_values_valid(self, mocker, tags, songrecord, dry_run, target):
        tags.track = None
        target(songrecord=songrecord, tags=tags, dry_run=dry_run)

        assert tags.track == 7
        assert len(tags.audiofile.tag.save.mock_calls) == 0 if dry_run else 1

    @pytest.mark.parametrize('original,expect', [
        ('08 - Open Car', '08 - Open Car'),
        ('Open Car', '07 - Open Car'),
        ('8 - Open Car.mp3', '08 - Open Car.mp3'),
        ('Open Car.mp3', '07 - Open Car.mp3'),
    ])
    def test_target_filename_valid(self, tags, songrecord, original, expect, target):
        tags.filepath = tags.filepath.parent / original
        tags.title = tags.filepath.name
        songrecord.title = tags.title
        assert target(songrecord=songrecord, tags=tags).target_filename == expect
