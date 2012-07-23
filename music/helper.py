import os, datetime
import mutagen as tagreader

from django.utils.timezone import utc

from music.models import Song

def dbgprint(*args):
    """
    When run as wsgi, there will be strange UnicodeErrors unless you decode it yourself.
    When run as local server, you won't see the problems"
    However, never use print, but dbgprint!
    """

    message = ""  # is a str
    try:
        for m in args:
            if type(m) == unicode:
                m = m.encode("utf-8")  # create a str from unicode, but encode it before
            else:
                m = str(m)  # make a str from element

            message = message + m + " "

        print message

    except Exception, e:
        print "EXCEPTION in dbgprint: Crappy string or unicode to print! This will be difficult to debug!"

def add_song(dirname, files, user):
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
            tags = tagreader.File(path, easy=True)
        except Exception, e:
            dbgprint("Error reading tags on file", path, e)
            processed += 1
            continue

        # ignore everything except ogg and mp3
        if type(tags) == tagreader.oggvorbis.OggVorbis:
            mime = "audio/ogg"
        elif type(tags) == tagreader.mp3.EasyMP3:
            mime = "audio/mp3"
        elif type(tags) == type(None):
            # don't even warn
            processed += 1
            continue
        else:
            # dbgprint("Ignoring file", path, "because of mime (", type(tags), ")")
            processed += 1
            continue

        try:
            artist    = tags['artist'][0].encode('utf-8')
            if not len(artist)>0:
                artist = "Unknown Artist"
        except:
            artist = "Unknown Artist"

        try:
            title     = tags['title'][0].encode('utf-8')
            if not len(title)>0:
                title = "Unknown Title"
        except:
            title = "Unknown Title"

        try:
            track     = int(tags['tracknumber'][0].encode('utf-8').split('/')[0])
        except:
            track = 0

        try:
            album     = tags['album'][0].encode('utf-8')
            if not len(album)>0:
                album = "Unknown Album"
        except:
            album = "Unknown Album"

        if song == None:
            # new song item
            dbgprint("Adding file ", path)
            song = Song(
                    artist    = artist,
                    title     = title,
                    album     = album,
                    track     = track,
                    mime      = mime,
                    user      = user,
                    path_orig = path,
                    timestamp_orig = timestamp,
                    )
        else:
            # overwrite old song item
            dbgprint("Updating file ", path)
            song.artist    = artist
            song.title     = title
            song.album     = album
            song.track     = track
            song.mime      = mime
            song.user      = user
            song.path_orig = path
            song.timestamp_orig = timestamp

        try:
            song.save()
        except Exception, e:
            dbgprint("Database error on file", path, e)

        processed += 1

    return processed
