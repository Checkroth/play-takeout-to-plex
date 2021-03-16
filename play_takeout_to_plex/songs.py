import html
import logging
from pathlib import Path
from dataclasses import dataclass, field

import eyed3

# Arbitrary length at which google takeout cuts off song titles etc.
MAX_FILENAME_LEN = 47
SHORTENED_FILENAME_LEN = MAX_FILENAME_LEN - 5


logger = logging.getLogger(__name__)


@dataclass
class SongRecord:
    title: str
    album: str
    artist: str
    duration_ms: int
    rating: int
    play_count: int
    removed: bool
    original_csv_name: str

    def __post_init__(self):
        self.duration_ms = int(self.duration_ms)
        self.rating = int(self.rating)
        self.play_count = int(self.play_count)
        self.removed = bool(self.removed)
        self.title = html.unescape(self.title)
        self.album = html.unescape(self.album)
        self.artist = html.unescape(self.artist)

    def __str__(self):
        return ','.join([
            self.title,
            self.album,
            self.artist,
            str(self.duration_ms),
            str(self.rating),
            str(self.play_count),
            str(self.removed) if self.removed else ''])


@dataclass
class SongTags:
    filepath: Path
    track: int = field(init=False)
    title: str = field(init=False)
    album: str = field(init=False)
    artist: str = field(init=False)
    audiofile: eyed3.core.AudioFile = field(init=False)
    pull_tags: bool = True

    def __post_init__(self):
        if self.pull_tags:
            self.audiofile = eyed3.load(self.filepath)
            try:
                # 2-tuple (track_num, total_tracks)
                self.track = self.audiofile.tag.track_num[0]
            except (IndexError, TypeError):
                self.track = self.audiofile.tag.track_num
            self.title = self.audiofile.tag.title
            self.album = self.audiofile.tag.album
            self.artist = self.audiofile.tag.artist

    @property
    def title_track_num(self):
        try:
            # Will catch '01', '11', '1 ', etc.
            track_num = int(self.title.split(' - ')[0])
        except ValueError:
            # Can reasonably say track title does not start with the track number.
            track_num = None

        return track_num

    @property
    def has_title_extension(self):
        return bool(Path(self.title).suffixes)


@dataclass
class RecordTagLink:
    songrecord: SongRecord
    tags: SongTags
    dry_run: bool = True

    @property
    def target_filename(self):
        try:
            if not self.tags.title_track_num:
                # Prepend the track number to the track only if it isn't already there.
                track_portion = self.tags.track
                title_portion = self.tags.title
            else:
                track_portion = self.tags.title_track_num
                title_portion = self.tags.title.split(' - ', 1)[-1]
        except IndexError:
            track_portion = None
            title_portion = self.tags.title

        if track_portion:
            track_portion = str(track_portion).zfill(2)
        extension = (self.tags.filepath.suffixes[-1]
                     if self.tags.filepath.suffixes and not self.tags.has_title_extension
                     else None)
        filename = ' - '.join(filter(None, [track_portion, title_portion]))
        return ''.join(filter(None, [filename, extension]))

    def __post_init__(self):
        if ((self.songrecord.artist, self.songrecord.album, self.songrecord.title)
                != (self.tags.artist, self.tags.album, self.tags.title)):
            raise Exception('Tag and record from CSV not properly linked')

        tags_updated = []
        if not self.tags.track and self.tags.title_track_num:
            self.tags.track = self.tags.title_track_num
            self.tags.audiofile.tag.track_num = self.tags.title_track_num
            tags_updated.append(self.tags.title_track_num)

        if tags_updated:
            logger.info(
                'tags_updated file=%s tags=%s dry_run=%d',
                self.tags.filepath.name,
                tags_updated,
                int(self.dry_run),
            )

            if not self.dry_run:
                self.tags.audiofile.tag.save()
