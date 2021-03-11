=================================
Google Play Music Takeout to Plex
=================================

A tool for restructuring Google Play Music Takeout to a plex (and human)-friendly format.

This tool comes with zero garuntees. I recommend testing on a small subset of audio files before attempting it on a full takeout library.

The first step of the tool scrapes all of the google play CSV files and turns them in to one main csv. This will be output even during dry run, and can be used on its own in this way.

=================================
Usage
=================================

``python takeout_converter.py --takeout-tracks-directory 'google_extract/Takeout/Google Play Music/Tracks/'``

=================================
Options
=================================

.. list-table:: Options
   :header-rows: 1

   * - name
     - type
     - required
     - description
   * - -i/--takeout-tracks-directory
     - string
     - yes
     - the directory containing extracted takeout files (audio files and csv files
   * - dry-run
     - any value
     - no
     - skip actually operating on files if anything is passed. Will still output the main-csv file.
   * - move-files
     - any value
     - no
     - moves files instead of copying them. Useful if you have limited space.
   * - main-csv
     - string
     - no
     - filepath to a csv that combines all play takeout files. Mostly for debugging. CSV that can be used here is output by the program.
   * - output-directory
     - string
     - no
     - Directory to which to move or copy the audio files. defaults to 'out'

=================================
Output
=================================

The tool scrapes the google play music CSVs and the audio files' metadata.

Actual metadata is prioritized, but if metadata is missing but is present in the CSV (artist, album, track name), it will be added to the audio file.

Files are then moved to directories underneath ``out``, or the supplied ``takeout-tracks-directory`` location.



The directory structure follows `Plex music directory and file naming <https://support.plex.tv/articles/200265296-adding-music-media-from-folders>`_.

Based on play csvs and file metadata, they will be structured to be: ``ArtistName/AlbumName/TrackNumber - TrackName.ext``
