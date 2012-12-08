import os, datetime
import mutagen as tagreader

from django.utils.timezone import utc
from django.utils import simplejson
from django.conf import settings
from django.db import transaction
from django.db.models import Q

from music.models import Song, Artist, Album, Genre, MusicSession

STACKTRACE = None

DEFAULT_BROWSE_COLUMNS_AVAILABLE = [
            {"order": "0", "name":"genre",  "show": True},
            {"order": "1", "name":"artist", "show": True},
            {"order": "2", "name":"album",  "show": True},
]

user_status_defaults = simplejson.dumps({
    "current_view":             "collection",
    "current_view_playlist":    0,

    "current_source":           "collection",
    "current_song_id":          0,
    "current_playlist_id":      0,
    "current_item_id":          0,

    "collection_search_terms":  "",

    "browse_column_display":    DEFAULT_BROWSE_COLUMNS_AVAILABLE,
    "browse_selected_album":   [],
    "browse_selected_artist":  [],
    "browse_selected_genre":   [],
})


class UserStatus():

    def __init__(self, request):
        self.music_session = MusicSession.objects.get(user=request.user)

    def get(self, key, default=None):

        try:
            vals = simplejson.loads(self.music_session.status)
        except ValueError:
            vals = dict()

        if key in vals:
            return vals[key]
        else:
            if default != None:
                vals[key] = default
                self.music_session.status = simplejson.dumps(vals)
                self.music_session.save()

            return default

    def set(self, key, value):
        try:
            tmp = simplejson.loads(self.music_session.status)
        except ValueError:
            tmp = dict()

        tmp[key] = value
        self.music_session.status = simplejson.dumps(tmp)
        self.music_session.save()

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
    Returns song query based on search terms in user_status. search_terms will be split 
    on " " in single terms. terms are treated with AND

    The following fields will be search:
    song.artist, song.title, song.album, song.mime, song.genre

    If browse = True the selection of browse fields will be respected.
    """

    user_status = UserStatus(request)
    if not browse:
        terms = user_status.get("collection_search_terms", "").strip()

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
            perfomrer = tags['performer'][0]
        except:
            performer = None
    else:
        performer = None

    if "albumartist" in tags.keys():
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
            'perfomer': performer,
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


def get_column_order(column_name, user_columns):
    # return order number of column_name in user_status
    # user_columns must be something like DEFAULT_BROWSE_COLUMNS_AVAILABLE

    column_order = 0 # avoid exception because of undefined variable
    for column_settings in user_columns:
        if column_settings["name"] == column_name:
            column_order = column_settings["order"]

    return column_order


def get_columns_to_render(column_begin_order, user_status, unset_following=False):
    # Determine columns to render. Remember filter of previous columns.
    # Create a list with correct order.
    # unset_following: Unset filter of later columns.
    # column_begin_order: order number of column to start with
    #
    # returns: [{'name': "a column name", 'selected', [pk, pk, pk]}, {....}, ...]

    global DEFAULT_BROWSE_COLUMNS_AVAILABLE

    user_columns = user_status.get("browse_column_display", DEFAULT_BROWSE_COLUMNS_AVAILABLE)

    columns_filter = []
    last_order = 1000
    for column_settings in user_columns:

        if column_settings["show"]:

            current_order  = column_settings["order"]
            name           = column_settings["name"]

            # clear selection of subsequent columns
            if current_order > column_begin_order:
                selected = []
                if unset_following:
                    user_status.set("browse_selected_%s" % name, [])
            else:
                selected = user_status.get("browse_selected_%s" % name, [])

            filter_item = {
                "name": name,           # the column name
                "selected": selected,
            }

            if last_order < current_order:
                columns_filter.append(filter_item)
            else:
                columns_filter.insert(0, filter_item )

            last_order = current_order

    return columns_filter


def prepare_browse_queries(columns_filter):
    # create queries
    queries_song = []
    for ii, col_filter in enumerate(columns_filter):
        if col_filter["name"] == "genre":
            # get only selected genre entries
            queries_genre = [Q(pk=pk) for pk in col_filter["selected"]]
            [queries_song.append(Q(genre__pk=pk)) for pk in col_filter["selected"]]

            # refine genre column entries based on selection in previous columns
            for jj in range(ii):
                if   columns_filter[jj]["name"] == "artist": [ queries_genre.append(Q(song__artist__pk=pk)) for pk in columns_filter[jj]["selected"] ]
                elif columns_filter[jj]["name"] == "album":  [ queries_genre.append(Q(song__album__pk=pk))  for pk in columns_filter[jj]["selected"] ]

        elif col_filter["name"] == "artist":
            # get only selected artist entries
            queries_artist = [Q(pk=pk) for pk in col_filter["selected"]]
            [queries_song.append(Q(artist__pk=pk)) for pk in col_filter["selected"]]

            # refine artist column entries based on selection in previous columns
            for jj in range(ii):
                if   columns_filter[jj]["name"] == "genre":  [ queries_artist.append(Q(song__genre__pk=pk)) for pk in columns_filter[jj]["selected"] ]
                elif columns_filter[jj]["name"] == "album":  [ queries_artist.append(Q(song__album__pk=pk)) for pk in columns_filter[jj]["selected"] ]

        elif col_filter["name"] == "album":
            # get only selected album entries
            queries_album = [Q(pk=pk) for pk in col_filter["selected"]]
            [queries_song.append(Q(album__pk=pk)) for pk in col_filter["selected"]]


            # refine album column entries based on selection in previous columns
            for jj in range(ii):
                if   columns_filter[jj]["name"] == "genre":  [ queries_album.append(Q(song__genre__pk=pk))  for pk in columns_filter[jj]["selected"] ]
                elif columns_filter[jj]["name"] == "artist": [ queries_album.append(Q(song__artist__pk=pk)) for pk in columns_filter[jj]["selected"] ]


    return {'genre': queries_genre, 'artist': queries_artist, 'album': queries_album, 'song': queries_song}
