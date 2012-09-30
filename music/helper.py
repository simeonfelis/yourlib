import os, datetime
import mutagen as tagreader

from django.utils.timezone import utc
from django.utils import simplejson
from django.conf import settings
from django.db import transaction
from django.db.models import Q

from music.models import Song, Artist, Album, Genre, MusicSession

STACKTRACE = None

DEFAULT_BROWSE_COLUMN_ORDER = ['artist', 'album', 'title']

user_status_defaults = simplejson.dumps({
    "search_terms": "",
    "browse_column_order": DEFAULT_BROWSE_COLUMN_ORDER,
    "browse_selected_albums": [],
    "browse_selected_artists": [],
})


class UserStatus():

    def __init__(self, request):
        self.music_session = MusicSession.objects.get(user=request.user)
        self.vals = simplejson.loads(self.music_session.status)  # initial population

    def get(self, key, default=None):

        self.vals = simplejson.loads(self.music_session.status)

        if key in self.vals:
            return self.vals[key]
        else:
            self.vals[key] = default
            self.music_session.status = simplejson.dumps(self.vals)
            self.music_session.save()

            return default

    def set(self, key, value):
        tmp = simplejson.loads(self.music_session.status)

        tmp[key] = value
        self.music_session.status = simplejson.dumps(tmp)
        self.music_session.save()
        self.vals = tmp

def browse_column_album(request):
    """
    Returns [albums,songs] based on a selection of artists.
    the selection has to be in the UserStatus.
    If nothing is selected, returns all songs and albums from user.
    This function depends on static column order.
    """
    songs  = Song.objects.select_related().filter(user=request.user).order_by("artist__name", "album__name", "track")
    albums = Album.objects.filter(song__user=request.user).distinct().order_by("name")

    # find out what the user has selected
    user_status = UserStatus(request)
    items = user_status.get("browse_selected_artists", None)

    # Build query to retrieve the albums
    # TODO: find out which other columns to filter. song title might not be the only one
    if items and len(items):
        queries_albums = [ Q(song__artist__id=pk) for pk in items]
        queries_songs  = [ Q(      artist__id=pk) for pk in items]
        query_albums = queries_albums.pop()
        query_songs  = queries_songs.pop()
        for q in queries_albums:
            query_albums |= q
        for q in queries_songs:
            query_songs |= q

        songs  = songs.filter(query_songs)
        albums = albums.filter(query_albums)
    else:
        # already fetched all
        pass

    return albums, songs

def browse_column_title(request):
    """
    Returns songs based on a selection of artists and albums.
    The selection has to be stored in UserStatus.
    If nothing is selected, returns all songs from user.
    This function depends on static column order.
    """
    songs   = Song.objects.select_related().filter(user=request.user).order_by("artist__name", "album__name", "track")

    # find out what the user has selected
    user_status  = UserStatus(request)
    album_items  = user_status.get("browse_selected_albums", None)
    artist_items = user_status.get("browse_selected_artists", None)

    if album_items and len(album_items):
        queries = [ Q(album__id=pk) for pk in album_items]
        query = queries.pop()
        for q in queries:
            query |= q

        songs = songs.filter(query).order_by("artist__name", "album__name", "track")

    if artist_items and len(artist_items):
        queries = [ Q(artist__id=pk) for pk in artist_items]
        query = queries.pop()
        for q in queries:
            query |= q

        songs = songs.filter(query).order_by("artist__name", "album__name", "track")

    return songs

def search(request, browse=False):
    """
    Returns songs based on search terms in user_status. search_terms will be split 
    on " " in terms and terms are treated with AND

    The following fields will be search:
    song.artist, song.title, song.album, song.mime, song.genre

    If browse = True the selection of browse fields will be respected.
    """

    user_status = UserStatus(request)
    terms = user_status.get("search_terms", "").strip()

    songs = Song.objects.select_related().filter(user=request.user).order_by("artist__name", "album__name", "track")

    if browse:
        album_items  = user_status.get("browse_selected_albums", None)
        artist_items = user_status.get("browse_selected_artists", None)

        if album_items and len(album_items):
            queries = [ Q(album__id=pk) for pk in album_items]
            query = queries.pop()
            for q in queries:
                query |= q

            songs = songs.filter(query)

        if artist_items and len(artist_items):
            queries = [ Q(artist__id=pk) for pk in artist_items]
            query = queries.pop()
            for q in queries:
                query |= q

            songs = songs.filter(query)

    elif len(terms) > 0:
        term_list = terms.split(" ")

        songs = songs.filter(Q(artist__name__icontains=term_list[0]) | \
                                    Q(title__icontains=term_list[0]) | \
                                    Q(album__name__icontains=term_list[0]) | \
                                    Q(genre__name__icontains=term_list[0]) | \
                                    Q(mime__icontains=term_list[0]))
        for term in term_list[1:]:
            songs = songs.filter(Q(artist__name__icontains=term) | \
                                 Q(title__icontains=term) | \
                                 Q(album__name__icontains=term) | \
                                 Q(genre__name__icontains=term) | \
                                 Q(mime__icontains=term))

    return songs

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

    if "artist" in tags:
        try:
            artist    = tags['artist'][0] #.encode('utf-8')
            if not len(artist)>0:
                artist = None
        except:
            artist = None
    else:
        artist = None

    if "performer" in tags.keys():
        try:
            albumartist = tags['performer'][0]
        except:
            albumartist = None

    elif "albumartist" in tags.keys():
        try:
            albumartist = tags['performer'][0]
        except:
            albumartist = None
    else:
        albumartist = None

    if "year" in tags.keys():
        try:
            year = tags['year'][0]
        except:
            year = None
    else:
        year = None

    try:
        title     = tags['title'][0] #.encode('utf-8')
        if not len(title)>0:
            title = os.path.split(path)[-1]
    except:
        title = os.path.split(path)[-1]

    try:
        track     = int(tags['tracknumber'][0].encode('utf-8').split('/')[0])
    except:
        track = 0

    try:
        genre     = tags['genre'][0]
    except:
        genre = None

    try:
        length = int(tags.info.length)
    except:
        length = 0

    try:
        album     = tags['album'][0] #.encode('utf-8')
        if not len(album)>0:
            album = None
    except:
        album = None


    tags = {
            'artist': artist,
            'albumartist': albumartist,
            'album' : album,
            'track': track,
            'title': title,
            'genre': genre,
            'length': length,
            'year': year,
            'mime': mime,
            }

    return tags

def set_song(tags, timestamp, user, path, song):
    # if song == None, returns a new Song object.
    # song must be explicitly saved after that function
    # returns changed or new Song object instance
    # also creates corresponding foreign key dependencies

    album = None
    if tags['album']:
        try:
            album = Album.objects.get(name=tags['album'])
        except Album.DoesNotExist:
            album = Album(name = tags['album'])
            try:
                album.save()
            except:
                album = None
        except Exception, e:
            print("Error checking for existing album:", tags['album'], e)

    genre = None
    if tags['genre']:
        try:
            genre = Genre.objects.get(name=tags['genre'])
        except Genre.DoesNotExist:
            genre = Genre(name = tags['genre'])
            try:
                genre.save()
            except:
                genre = None

    artist = None
    if tags['artist']:
        try:
            artist = Artist.objects.get(name=tags['artist'])
        except Artist.DoesNotExist:
            artist = Artist(name = tags['artist'])
            try:
                artist.save()
            except:
                artist = None

    year = tags['year']

    if not song == None:
        song.title     = tags['title']
        song.track     = tags['track']
        song.mime      = tags['mime']
        song.length    = tags['length']
        song.year      = year
        song.genre     = genre
        song.album     = album
        song.artist    = artist
        song.user      = user
        song.path_orig = path
        song.time_changed = timestamp
        song.time_added = datetime.datetime.now().replace(tzinfo=utc)
    else:
        song = Song(
             title     = tags['title'],
             track     = tags['track'],
             mime      = tags['mime'],
             length    = tags['length'],
             year      = year,
             artist    = artist,
             album     = album,
             genre     = genre,
             user      = user,
             path_orig = path,
             time_changed = timestamp,
             time_added = datetime.datetime.now().replace(tzinfo=utc),
             )
    return song

@transaction.autocommit
def update_song(song):
    """
    re-reads tags of song and saves it
    """

    timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(song.path_orig)).replace(tzinfo=utc)

    if song.time_changed == timestamp:
        return

    try:
        tags = get_tags(song.path_orig)
    except Exception, e:
        dbgprint("update_song: error reading tags on file", song.path_orig, ":", e)
        return

    set_song(tags, timestamp, song.user, song.path_orig, song)

    try:
        song.save()
    except Exception, e:
        dbgprint("update_song: error saving entry", song, ":", e)
        raise e

@transaction.commit_manually
def add_song(dirname, files, user, force=False):
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

        try:
            # To bulletproof the os.walk() call, str is used for paths.
            # But we need unicode for the db. If conversion fails, the file
            # path has some funny encoding which I can't understand.
            # replacing won't help(?), as we need an exact file path
            # path = path.decode('utf-8', "replace")
            path = path.decode('utf-8')
        except UnicodeDecodeError:
            print("add_song: Ignoring UnicodeDecodeError on", path)
            processed += 1
            continue

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
            if not force and song.time_changed == timestamp:
                processed += 1
                continue
            else:
                # reread tags and store it to song. Therefore, leave variable song != None
                pass
        transaction.commit()

        try:
            tags = get_tags(path)
        except Exception, e:
            #dbgprint("Error reading tags on file", path, e)
            processed += 1
            continue
        else:
            if tags == None:
                #dbgprint("add_song: no tags in file", path)
                processed += 1
                continue

        try:
            song = set_song(tags, timestamp, user, path, song)
        except Exception, e:
            transaction.rollback()
            print("Error during set_song for file", path, e)
            processed += 1
            continue
        else:
            transaction.commit()

        try:
            song.save()
        except Exception, e:
            transaction.rollback()
            print("Exception in add_song: Database error on file", path, ":", e)
        else:
            transaction.commit()

        processed += 1

    return processed
