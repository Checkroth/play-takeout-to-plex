import html

import eyed3

# Arbitrary length at which google takeout cuts off song titles etc.
MAX_FILENAME_LEN = 47
SHORTENED_FILENAME_LEN = MAX_FILENAME_LEN - 5


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
        self.removed = bool(self.removed)  # TODO:: don't actually know what this is other than empty

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
        return re.sub('[^a-zA-Z0-9 \n\.\-]', "_", html.unescape(s))

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
    def __init__(self, filepath: Path, songrecord: SongRecord, dry_run=False):
        audiofile = eyed3.load(filepath)
        super(
            songrecord=songrecord,
            audiofile=audiofile,
            filepath=filepath,
            track=audiofile.tag.track_num,
            title=audiofile.tag.title,
            album=audiofile.tag.album,
            artist=audiofile.tag.artist,
        )
        self.dry_run = dry_run

    songrecord: SongRecord
    audiofile: eyed3.core.AudioFile
    filepath: Path
    track: int
    title: str
    album: str
    artist: str

    @property
    def title_track_num(self):
        try:
            # Will catch '01', '11', '1 ', etc.
            track_num = int(self.filepath.name[:2])
        except ValueError:
            # Can reasonably say track title does not start with number.
            track_num = None

        return track_num

    def __post_init__(self):
        tags_updated = False
        if not self.track and self.title_track_num:
            self.track = self.title_track_num
            self.audiofile.tag.track_num = self.track
            tags_updated = True

        if not self.title and self.songrecord.title:
            title = html.unescape(self.songrecord.title)
            self.title = title
            self.audiofile.tag.title = title
            tags_updated = True

        if not self.album and self.songrecord.album:
            album = html.unescape(self.songrecord.album)
            self.album = album
            self.audiofile.tag.album = album
            tags_updated = True

        if not self.artist and self.songrecord.artist:
            artist = html.unescape(self.songrecord.artist)
            self.artist = artist
            self.audiofile.tag.artist = artist
            tags_updated = True

        if tags_updated and not self.dry_run:
            self.audiofile.tag.save()


@dataclass
class RecordTagLink:
    # TODO:: Move the tag updating based on google audiofile info to here,
    # so we can fetch tags and search for google CSV without the circular dependency.
    record: SongRecord
    tags: SongTags

    def __post_init__(self):
        if (self.record.album, self.record.title) != (self.tags.album, self.tags.title):
            raise Exception('Tag and record from CSV not properly linked')
