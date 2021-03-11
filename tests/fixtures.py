from io import StringIO
from play_takeout_to_plex.songs import SongRecord


HEADER_ROW = 'Title,Album,Artist,Duration (ms),Rating,Play Count,Removed\r\n'
CSV_RECORDS = [
    SongRecord(title='03 - I Shot The Sheriff.mp3', album='Live From London', artist='Bob Marley',
               duration_ms=314000, rating=0, play_count=1, removed=False, original_csv_name=''),
    SongRecord(title='05 - I Shot The Sheriff.mp3', album="Burnin'", artist='Bob Marley',
               duration_ms=282000, rating=0, play_count=0, removed=False, original_csv_name=''),
    SongRecord(title='05 - I Shot The Sheriff.mp3', album='Live at Rockpalast', artist='Bob Marley',
               duration_ms=277000, rating=0, play_count=1, removed=False, original_csv_name=''),
    SongRecord(title='06 - I Shot The Sheriff.mp3', album='Live!', artist='Bob Marley',
               duration_ms=315000, rating=0, play_count=1, removed=False, original_csv_name=''),
    SongRecord(title='06 - I Shot The Sheriff.mp3', album='Live at the Lyceum', artist='Bob Marley',
               duration_ms=315000, rating=0, play_count=0, removed=False, original_csv_name=''),
    SongRecord(title='07 - I Shot The Sheriff.mp3', album='Legend', artist='Bob Marley',
               duration_ms=283000, rating=0, play_count=2, removed=False, original_csv_name=''),
    SongRecord(title='C-C-C-Cinnamon Lips', album='OK Go', artist='OK Go',
               duration_ms=207000, rating=0, play_count=26, removed=False, original_csv_name=''),
    SongRecord(title='Couch Potato', album='Poodle Hat', artist='Weird Al Yankovic',
               duration_ms=258136, rating=0, play_count=8, removed=False, original_csv_name=''),
    SongRecord(title='Open Car', album='Deadwing', artist='Porcupine Tree',
               duration_ms=228414, rating=0, play_count=9, removed=False, original_csv_name=''),
    SongRecord(title='White & Nerdy', album='Straight Outta Lynwood', artist='Weird Al Yankovic',
               duration_ms=170271, rating=0, play_count=0, removed=False, original_csv_name=''),
]

CSV_FILES = [
    StringIO(f'{HEADER_ROW}{row}')
    for row in CSV_RECORDS
]
