import os, datetime
import mutagen as tagreader

from django.utils.timezone import utc
from django.conf import settings

from music.models import Song

STACKTRACE = None

def dbgprint(*args):
    """
    When run as wsgi, there will be strange UnicodeErrors unless you decode it yourself.
    When run as local server, you won't see the problems
    However, never use print, but dbgprint!
    """
    global STACKTRACE

    if STACKTRACE == None:
        STACKTRACE = open(os.path.join(settings.BASE_PATH, 'STACKTRACE'), 'wb+')

    message = ""  # is a str
    try:
        for m in args:
            if type(m) == unicode:
                m = m.encode("utf-8")  # create a str from unicode, but encode it before
            else:
                m = str(m)  # make a str from element

            message = message + m + " "

        STACKTRACE.write(message + "\n")
        STACKTRACE.flush()
        os.fsync(STACKTRACE)

    except Exception, e:
        STACKTRACE.write("EXCEPTION in dbgprint: Crappy string or unicode to print! This will be difficult to debug!")
        STACKTRACE.write("\n")
        STACKTRACE.write("Trying to print the string here:")
        STACKTRACE.write(e)
        STACKTRACE.flush()
        os.fsync(STACKTRACE)

def get_tags(path):
    """
    returns tags as dicts or None if no tags found in file
    throws exceptions on file (path) errors
    """
    tags = tagreader.File(path, easy=True)

    # ignore everything except ogg and mp3
    if type(tags) == tagreader.oggvorbis.OggVorbis:
        mime = "audio/ogg"
    elif type(tags) == tagreader.mp3.EasyMP3:
        mime = "audio/mp3"
    elif type(tags) == type(None):
        # don't even warn
        return
    else:
        # dbgprint("Ignoring file", path, "because of mime (", type(tags), ")")
        return

    dbgprint("get_tags: analysing file", path)

    try:
        artist    = tags['artist'][0] #.encode('utf-8')
        if not len(artist)>0:
            artist = "Unknown Artist"
    except:
        artist = "Unknown Artist"

    try:
        title     = tags['title'][0] #.encode('utf-8')
        if not len(title)>0:
            title = "Unknown Title"
    except:
        title = os.path.split(path)[-1]

    try:
        track     = int(tags['tracknumber'][0].encode('utf-8').split('/')[0])
    except:
        track = 0

    try:
        album     = tags['album'][0] #.encode('utf-8')
        if not len(album)>0:
            album = "Unknown Album"
    except:
        album = "Unknown Album"

    tags = {
            'artist': artist,
            'album' : album,
            'track': track,
            'title': title,
            'mime': mime,
            }

    return tags

def set_song(tags, timestamp, user, path, song):
    # if song == None, returns a new Song object
    # song must be explicitly saved after that function
    # returns changed or new Song object instance

    if not song == None:
        song.artist    = tags['artist'],
        song.title     = tags['title'],
        song.album     = tags['album'],
        song.track     = tags['track'],
        song.mime      = tags['mime'],
        song.user      = user
        song.path_orig = path
        song.timestamp_orig = timestamp
    else:
        song = Song(
             artist    = tags['artist'],
             title     = tags['title'],
             album     = tags['album'],
             track     = tags['track'],
             mime      = tags['mime'],
             user      = user,
             path_orig = path,
             timestamp_orig = timestamp,
             )
    return song

def update_song(song):
    """
    re-reads tags of song and saves it
    """

    timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(song.path_orig)).replace(tzinfo=utc)

    if song.timestamp_orig == timestamp:
        return

    try:
        tags = get_tags(song.path_orig)
    except Exception, e:
        dbgprint("update_song: error reading tags on file", song.path_orig, ":", e)

    set_song(tags, timestamp, song.user, song.path_orig, song)

    try:
        song.save()
    except Exception, e:
        dbgprint("update_song: error saving entry", song, ":", e)

def add_song(dirname, files, user):
    """
    Takes a directory and one or more file names in that directory, reads tag information
    and adds the songs to the database for the given user.
    Invalid files or unsupported files are ignored.
    dirname must be string or os.path
    files must be array []

    If the given file path(s) are already in the database, it compares their timestamps
    and if they are not equal, the tags are read out again (->Performance)

    Returns the number of processed files, including eventually invalid and unsupported
    files.
    """

    processed = 0
    for filename in files:
        path = os.path.join(dirname, filename)

        if not os.path.isfile(path):
            processed += 1
            continue

        timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(path)).replace(tzinfo=utc)
        # check for duplicates resp. file change. if timestamp has change, re-read tags
        song = None
        try:
            song = Song.objects.get(path_orig=path)
        except Song.DoesNotExist:
            pass
        else:
            # file already in database
            if song.timestamp_orig == timestamp:
                processed += 1
                continue
            else:
                # reread tags and store it to song. Therefore, leave variable song != None
                pass

        try:
            tags = get_tags(path)
        except Exception, e:
            dbgprint("Error reading tags on file", path, e)
            processed += 1
            continue
        else:
            if tags == None:
                #dbgprint("add_song: no tags in file", path)
                processed += 1
                continue

        song = set_song(tags, timestamp, user, path, song)

        try:
            song.save()
        except Exception, e:
            dbgprint("Database error on file", path, ":", e)

        processed += 1

    return processed
