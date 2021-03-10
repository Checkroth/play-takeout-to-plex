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

    def _escape(self, s):
        return re.sub('[^a-zA-Z0-9 \\n\.\-]', "_", s)

    @property
    def expect_songfile(self):
        return f'{self.artist} - {self._escape(album)} - {self._escape(title)}'

    @property
    def expect_songfile_start(self):
        '''
        Song filenames will Be in two formats. 
        - Artist - Album - Title.mp3
        - Artist - Album(###)shortened_title.mp3

        For organizational purposes, we only care about the portion up to the album.
        Calculation for the latter must be done in the event that
            the artist & album name is longer than MAX_FILENAME_LEN.

        The latter occurs when the full filename is greater than MAX_FILENAME_LEN.
        Filename is then calculated as follows:
        "song artist - album" up to MAX_FILENAME_LEN - 5 length + (
        Ex.: Weird Al Yankovic - Straight Outta Lynwood - White _ Nerdy = 58
        -> Weird Al Yankovic - Straight Outta Lynwood = 42 ( 47 - 5 )
        -> Weird Al Yankovic - Straight Outta Lynwood(###) = 47,
            Cannot guess the # in the filename, so starts with up to Lynwood(
        '''
        raw_start = f'{self.artist} - {self._escape(album)}'
        if len(raw_start) > SHORTENED_FILENAME_LEN:
            filestart = raw_start[:SHORTENED_FILENAME_LEN]
            filestart = f'{filestart}('
        else:
            filestart = raw_start
        
        return filestart


@dataclass
class SongTags:
    filepath: Path
    track: int = field(init=False)
    title: str = field(init=False) 
    album: str = field(init=False)
    artist: str = field(init=False)
    audiofile: eyed3.core.AudioFile = field(init=False)

    def __post_init__(self):
        self.audiofile = eyed3.load(self.filepath)
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
                track_portion = str(self.tags.track[0]).zfill(2)
            else:
                track_portion = None
        except IndexError:
            track_portion = None

        title_portion = self.tags.title or None
        extension = (self.tags.filepath.suffixes[-1]
                     if self.tags.filepath.suffixes and not self.tags.has_title_extension
                     else None)
        filename = ' - '.join(filter(None, [track_portion, title_portion]))
        return ''.join(filter(None, [filename, extension]))

    def __post_init__(self):
        if (self.songrecord.album, self.songrecord.title) != (self.tags.album, self.tags.title):
            import pdb; pdb.set_trace()
            raise Exception('Tag and record from CSV not properly linked')

        tags_updated = []
        if not self.tags.track and self.tags.title_track_num:
            self.tags.track = self.tags.title_track_num
            self.tags.audiofile.tag.track_num = self.tags.title_track_num
            tags_updated.append(self.tags.title_track_num)

        if not self.tags.title and self.songrecord.title:
            title = html.unescape(self.songrecord.title)
            self.tags.title = title
            self.tags.audiofile.tag.title = title
            tags_updated.append(title)

        if not self.tags.album and self.songrecord.album:
            album = html.unescape(self.songrecord.album)
            self.tags.album = album
            self.tags.audiofile.tag.album = album
            tags_updated.append(album)

        if not self.tags.artist and self.songrecord.artist:
            artist = html.unescape(self.songrecord.artist)
            self.tags.artist = artist
            self.tags.audiofile.tag.artist = artist
            tags_updated.append(artist)

        if tags_updated:
            logger.info(
                'tags_updated file=%s tags=%s dry_run=%d',
                self.tags.filepath.name,
                tags_updated,
                int(self.dry_run),
            )

            if not self.dry_run:
                self.audiofile.tag.save()
