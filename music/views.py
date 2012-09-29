from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.utils import simplejson
from django.db.models import Q
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse

from music.models import Song, Artist, Album, Genre, Playlist, PlaylistItem, MusicSession, Collection, Upload, Download
from music.forms import UploadForm
#from music.helper import dbgprint, UserStatus, user_status_defaults
from music import helper
from music import settings

import os

INITIAL_ITEMS_LOAD_COUNT = 50
SUBSEQUENT_ITEMS_LOAD_COUNT = 50

@login_required
def home_view(request):

    if not os.path.isdir(os.path.join(settings.MUSIC_PATH, request.user.username)):
        os.makedirs(os.path.join(settings.MUSIC_PATH, request.user.username))
    playlists = Playlist.objects.filter(user=request.user)
    # create playlists if not existent for user
    if 0 == len(playlists):
        helper.dbgprint("Creating default playlist for user ", request.user)
        pl = Playlist(name="default", user=request.user, current_position=0)
        pl.save()
        playlists = Playlist.objects.filter(user=request.user)

    # current status
    try:
        music_session = MusicSession.objects.get(user=request.user)
        user_status = helper.UserStatus(request)
    except MusicSession.DoesNotExist:

        helper.dbgprint("Creating music session for user ", request.user)
        music_session = MusicSession(
            status = helper.user_status_defaults,
            user=request.user,
            currently_playing='none',
            search_terms='',
            filter_show=False
        )
        music_session.save()

    if music_session.currently_playing == "playlist":
        cur_pos = music_session.current_playlist.current_position

        current_item = music_session.current_playlist.items.get(position=cur_pos)

        # the following is needed to prefill player data
        current_song = current_item.song
        current_item_id = current_item.id
        current_song_id = current_song.id
        current_playlist_id = music_session.current_playlist.id

    elif music_session.currently_playing == "collection":
        current_song = music_session.current_song
        current_song_id = current_song.id
        current_playlist_id = 0
        current_item_id = 0

    # create collection if not existent
    try:
        collection = Collection.objects.get(user=request.user)
    except Collection.DoesNotExist:
        collection = Collection(user=request.user, scan_status="idle")
        collection.save()

    songs = helper.search(request)
    songs_count = songs.count()
    if len(songs) > 10:
        songs = songs[:10]

    return render_to_response(
            'home.html',
            locals(),
            context_instance=RequestContext(request),
            )
##################### collection ##########################

@login_required
def collection_view(request):
    user_status = helper.UserStatus(request)

    songs = helper.search(request)
    songs_count = songs.count()

    if len(songs) > INITIAL_ITEMS_LOAD_COUNT:
        songs = songs[:INITIAL_ITEMS_LOAD_COUNT]
    return render_to_response(
            "context_collection.html",
            locals(),
            context_instance=RequestContext(request),
            )

@login_required
def collection_songs_view(request):

    so_far = int(request.POST.get("so_far", 0))

    songs = helper.search(request)
    songs_count = songs.count()

    if songs_count > so_far+SUBSEQUENT_ITEMS_LOAD_COUNT:
        songs = songs[so_far:so_far+SUBSEQUENT_ITEMS_LOAD_COUNT]
    else:
        songs = songs[so_far:]

    return render_to_response(
            "collection_songs_li.html",
            locals(),
            context_instance=RequestContext(request),
            )


@login_required
def collection_browse_view(request):

    # reset selections
    user_status = helper.UserStatus(request)
    user_status.set("browse_selected_albums", [])
    user_status.set("browse_selected_artists", [])

    songs   = Song.objects.select_related().filter(user=request.user).order_by("artist__name", "album__name")
    if songs.count() > INITIAL_ITEMS_LOAD_COUNT:
        songs = songs[:INITIAL_ITEMS_LOAD_COUNT]

    genres  = Genre.objects.filter(song__user=request.user).distinct().order_by("name", "name")
    if genres.count() > INITIAL_ITEMS_LOAD_COUNT:
        genres = genres[:INITIAL_ITEMS_LOAD_COUNT]

    artists = Artist.objects.filter(song__user=request.user).distinct().order_by("name")
    if artists.count() > INITIAL_ITEMS_LOAD_COUNT:
        artists = artists[:INITIAL_ITEMS_LOAD_COUNT]

    albums  = Album.objects.filter(song__user=request.user).distinct().order_by("name")
    if albums.count() > INITIAL_ITEMS_LOAD_COUNT:
        albums = albums[:INITIAL_ITEMS_LOAD_COUNT]


    columns = helper.DEFAULT_BROWSE_COLUMN_ORDER

    return render_to_response(
            "context_browse.html",
            locals(),
            context_instance=RequestContext(request),
            )

@login_required
def collection_browse_column_view(request, column_from):
    """
    Works in static column order only.

    If column_from is artist, returns list of albums and songs.
    If column_from is album, returns list of songs.

    The returned lists are filtered by the selection of the items in column_from. The item ids
    have to be transmitted in the POST request in "items[]". The selection will be stored
    in the user_status.
    """

    # Get the selected items
    if 'items[]' in request.POST:
        items = request.POST.getlist('items[]')
    else:
        items = None


    user_status = helper.UserStatus(request)
    if "artist" == column_from:
        # store selected items
        user_status.set("browse_selected_artists", items)

        # Set the columns to be rendered by templates
        columns = ["album", "title"]
        albums, songs = helper.browse_column_album(request)
        if albums.count() > INITIAL_ITEMS_LOAD_COUNT:
            albums = albums[:INITIAL_ITEMS_LOAD_COUNT]

    elif "album" == column_from:
        # store selected items
        user_status.set("browse_selected_albums", items)

        # Set the columns to be rendered by templates
        columns = ["title"]
        songs = helper.browse_column_title(request)

    else:
        return HttpResponse("Unsupported column: " + column_from)

    if songs.count() > INITIAL_ITEMS_LOAD_COUNT:
        songs = songs[:INITIAL_ITEMS_LOAD_COUNT]

    return render_to_response(
            "context_browse.html",
            locals(),
            context_instance=RequestContext(request),
            )


@login_required
def collection_browse_more_view(request, column):
    """
    Returns more items for `column` based on selection.
    Selection should be stored in user_settings previously.
    If nothing is selected, returns all items of list.
    """

    so_far = int(request.POST.get("so_far"))

    if "artist" == column:
        items = Artist.objects.filter(song__user = request.user).distinct()
    elif "album" == column:
        items, dump = helper.browse_column_album(request)
    elif "title" == column:
        items = helper.browse_column_title(request)

    items_count = items.count()

    if items_count > so_far+SUBSEQUENT_ITEMS_LOAD_COUNT:
        items = items[so_far:so_far+SUBSEQUENT_ITEMS_LOAD_COUNT]
    else:
        items = items[so_far:]

    if len(items) == 0:
        return HttpResponse("nomoreresults")


    if "artist" == column:
        artists = items
    elif "album" == column:
        albums = items
    elif "title" == column:
        songs = items


    return render_to_response(
            "browse_column_li.html",
            locals(),
            context_instance=RequestContext(request),
            )

def show_context_download(request):
    downloads = Download.objects.get(user=request.user)
    return render_to_response(
            "context_download.html",
            locals(),
            context_instance=RequestContext(request),
            )

def show_context_upload(request):
    uploads = Upload.objects.filter(user=request.user)

    form = UploadForm(request.POST)
    return render_to_response(
            "context_upload.html",
            locals(),
            context_instance=RequestContext(request),
            )

#def show_context_collection(request):
#    [songs, artists, albums] = get_filtered(request)
#    songs_count = songs.count()
#    if len(songs) > INITIAL_ITEMS_LOAD_COUNT:
#        songs = songs[:INITIAL_ITEMS_LOAD_COUNT]
#    return render_to_response(
#            "context_collection.html",
#            locals(),
#            context_instance=RequestContext(request),
#            )
#    # GET request collection
#    begin = int(request.GET.get('begin'), 0)
#    howmany = SUBSEQUENT_ITEMS_LOAD_COUNT
#    songs = filter_songs(request, terms=music_session.search_terms)
#    available = len(songs)
#    if begin < available:
#        if begin+howmany < available:
#            songs = songs[begin:begin+howmany]
#        else:
#            songs = songs[begin:available]
#    else:
#        return HttpResponse("")
#
#    return render_to_response(
#            "collection_songs_li.html",
#            locals(),
#            context_instance=RequestContext(request),
#            )

def show_context_playlist(request):
    if request.method == "POST":
        playlist_id = request.POST.get('playlist_id')
        playlist = Playlist.objects.get(id=playlist_id)
    else:
        playlist = Playlist.objects.get(user=request.user)

    return render_to_response(
            "context_playlist.html",
            locals(),
            context_instance=RequestContext(request),
            )

@login_required
def sidebar_show_view(request, context):

    music_session = MusicSession.objects.get(user=request.user)

    if context == "download":
        if request.method == "POST":
            music_session.context = "download"
            music_session.save()
        return show_context_download(request)

    elif context == "upload":
        if request.method == "POST":
            music_session.context = "upload"
            music_session.save()
        return show_context_upload(request)

    elif context == "collection":
        if request.method == "POST":
            music_session.context = "collection"
            music_session.save()
        return show_context_collection(request)

    elif context == "playlist":
        return show_context_playlist(request)

    return HttpResponse("")

#############################      upload     ##################################

@login_required
@csrf_exempt
@transaction.autocommit
def upload_view(request):
    if request.method == 'POST':
        if request.FILES == None:
            return HttpResponse("No files received")

        upfile = request.FILES[u'file']

        #################################  copying ################################
        helper.dbgprint("Entering status copying")
        step_status = 0

        userUploadStatus = Upload(user=request.user, step="copying", step_status=0)
        userUploadStatus.save()

        # determine user upload dir
        userupdir = os.path.join(
                settings.FILE_UPLOAD_USER_DIR,
                request.user.username
                )
        # create user's upload dir
        if not os.path.isdir(userupdir):
            os.makedirs(userupdir)

        # move temporary file to users's upload dir determine file name and path,
        # don't overwrite
        useruppath = os.path.join(userupdir, upfile.name)
        ii = 0
        while os.path.exists(useruppath):
            useruppath = os.path.join(
                    userupdir,
                    upfile.name + "_" + str(ii)
                    )
            ii += 1

        helper.dbgprint("Copy-to location:", useruppath, type(useruppath))

        # now put the upload content to the user's location
        step_status = 0
        processed = 0
        amount = upfile.size
        helper.dbgprint("Chunks:", amount)
        old_status = 0
        with open(useruppath, 'wb+') as destination:
            for chunk in upfile.chunks():
                processed += upfile.DEFAULT_CHUNK_SIZE
                destination.write(chunk)
                step_status = int(processed*100/amount)
                if (old_status < step_status) and (step_status % 2 == 0):
                    helper.dbgprint("Chunks copied:", step_status, "%")
                    userUploadStatus.step_status = step_status
                    userUploadStatus.save()
                    old_status = step_status
            destination.close()
        helper.dbgprint("Uploaded file written to", useruppath)

        # so here the upload is done and can be analyzed
        from music.tasks import upload_done
        upload_done.delay(useruppath, userupdir, userUploadStatus.id)

        uploads = Upload.objects.filter(user=request.user)
        return render_to_response(
                'upload_status.html',
                locals(),
                context_instance=RequestContext(request),
                )

    # return status on GET requests
    uploads = Upload.objects.filter(user=request.user)
    return render_to_response(
            'upload_status.html',
            locals(),
            context_instance=RequestContext(request),
            )

@login_required
def collection_search_view(request):

    if request.method == "POST":

        user_status = helper.UserStatus(request)

        if 'terms' in request.POST:
            terms = request.POST.get('terms', '')

            user_status.set("search_terms", terms)

            songs = helper.search(request)

            songs_count = songs.count()
            if len(songs) > INITIAL_ITEMS_LOAD_COUNT:
                songs = songs[:INITIAL_ITEMS_LOAD_COUNT]

            return render_to_response(
                    'collection_songs.html',
                    locals(),
                    context_instance=RequestContext(request),
                    )

    # return nothing on GET requests
    return HttpResponse("")

#############################      playlist stuff     ##################################

@login_required
def playlist_view(request):
    if request.method == "POST":
        playlist_id = request.POST.get('playlist_id')
        playlist = Playlist.objects.get(id=playlist_id)
    else:
        # get first playlist of the user the db gives us
        playlist = Playlist.objects.get(user=request.user)

    return render_to_response(
            "context_playlist.html",
            locals(),
            context_instance=RequestContext(request),
            )

@login_required
def sidebar_playlists_view(request):
    """
    return list of all playlists
    """
    playlists = Playlist.objects.filter(user=request.user)
    return render_to_response(
            'sidebar_playlists.html',
            locals(),
            context_instance=RequestContext(request),
            )

@login_required
@transaction.autocommit
def playlist_create_view(request):
    if request.method == "POST":
        name = request.POST.get('playlist_name')
        if not len(name) > 0:
            raise Exception("playlist name invalid: " + str(name))
        playlist = Playlist(name=name, user=request.user, current_position=0)
        playlist.save()
        playlists = Playlist.objects.filter(user=request.user)

        return render_to_response(
                "sidebar_playlists.html",
                locals(),
                context_instance=RequestContext(request),
                )

    return HttpResponse("")

@login_required
@transaction.autocommit
def playlist_delete_view(request):
    if request.method == "POST":

        playlist_id = request.POST.get('playlist_id')
        playlist = Playlist.objects.get(id=playlist_id)

        if playlist.name == "default":
            return HttpResponse("You can't delete the default playlist. it should stay.") # TODO: make a nice message

        playlist.delete()

        # return the first playlist of user
        [playlist] = Playlist.objects.filter(user=request.user)[0:1]

        return render_to_response(
                "context_playlist.html",
                locals(),
                context_instance=RequestContext(request),
                )

    return HttpResponse("")

@login_required
def playlist_append_view(request):
    if request.method == "POST":
        playlist_id  = request.POST.get("playlist_id")
        item_id      = request.POST.get("id")
        source       = request.POST.get("source")

        playlist = Playlist.objects.get(id=playlist_id)

        if "song" == source:
            songs = [Song.objects.get(user=request.user, id=item_id)]
        elif "artist" == source:
            songs = Song.objects.filter(user=request.user, artist__id=item_id)
        else:
            songs = []

        for song in songs:
            item = PlaylistItem(
                    song = song,
                    position = 1 + len(playlist.items.all())
                    )

            item.save()
            playlist.items.add(item)
            playlist.save()

        playlists = Playlist.objects.filter(user=request.user)

        return render_to_response(
                'sidebar_playlists.html',
                locals(),
                context_instance=RequestContext(request),
                )

    # Do not change anything on GET requests
    playlists = Playlist.objects.filter(user=request.user)
    return render_to_response(
            'playlists.html',
            locals(),
            context_instance=RequestContext(request),
            )

@login_required
def playlist_remove_item_view(request, playlist_id, item_id):

    playlist = Playlist.objects.get(id=playlist_id, user=request.user)

    if request.method == "POST":
        item = PlaylistItem.objects.get(id=item_id)
        position = item.position
        item.delete()
        # correct positions of all following items
        # TODO: this will be slow on large playlists, if item with low position number is removed
        for item in playlist.items.all().filter(position__gt=position):
            item.position = item.position-1
            item.save()
        playlist = Playlist.objects.get(id=playlist_id)


    # Do not change anything on GET requests
    return render_to_response(
            'playlist_songs.html',
            locals(),
            context_instance=RequestContext(request),
            )

@login_required
@transaction.autocommit
def playlist_reorder_view(request):
    # reorder algorithm was a saturday afternoon work. althoug sometimes slow,
    # the power of python made it beautiful. read it carefully, as it respects
    # the case if an item was moved to the very top (item_previous_id = "0") by
    # its cool queries (Q). also, item_moved_position is the original value,
    # but item_moved.position is going to be the new value

    if request.method == "POST":

        playlist_id         = request.POST.get('playlist_id')
        item_id             = request.POST.get('item_id')
        item_previous_id    = request.POST.get('item_previous_id')

        playlist            = Playlist.objects.get(user=request.user, id=playlist_id)
        item_moved          = PlaylistItem.objects.get(id=item_id)
        item_moved_position = item_moved.position

        if item_previous_id == "0":
            # This happens when moved to top
            item_previous_position = 0
        else:
            item_previous = PlaylistItem.objects.get(id=item_previous_id)
            item_previous_position = item_previous.position

        # TODO: this will be slow on large playlists, when moved from top to bottom (or vice versa)

        #print "reorder: in playlist", playlist.id, "item_previous_position", item_previous_position, "item_moved_position", item_moved_position

        # correct positions on items inbetween item_before and item (moved up)
        move_up = playlist.items.all().filter(Q(position__gt=item_previous_position) & Q(position__lt=item_moved_position))
        for item in move_up:
            #print "reorder: move up correcting position of", item
            item.position = item.position+1
            item.save()

        # correct positions on items inbetween item_before and item (moved down)
        move_down = playlist.items.all().filter(Q(position__lt=item_previous_position) & Q(position__gt=item_moved_position))
        for item in move_down:
            #print "reorder: move down correcting position of", item
            item.position = item.position-1
            item.save()

        # here, we have to correct the position of the item_previous element, if item_moved was moved below item_previous
        if (item_previous_position > item_moved_position) and not (item_previous_position == 0):
            #print "reorder: item_moved was moved below item_previous,I have to correct the positon of item_previous:", item_previous
            item_previous_position -= 1
            item_previous.position = item_previous_position
            item_previous.save()

        # correct the position of moved item itself:
        #print "reorder: correct position of item_moved:", item_moved
        item_moved.position = item_previous_position + 1
        item_moved.save()

        # if the item_moved is currently played, correct the status
        playlist = Playlist.objects.get(id=playlist_id, user=request.user)
        if playlist.current_position == item_moved_position: # compare with original value
            playlist.current_position = item_moved.position  # set new position
            playlist.save()


    return render_to_response(
            'playlist_songs.html',
            locals(),
            context_instance=RequestContext(request),
            )

def playlist_download(request):

#    if request.method == "POST":
#
#        download_start.send(None, request=request)
#        return HttpResponse("Your download request was sent to queue. It will appear in the download section")

    return HttpResponse("Only post request allowed")


###############################    player    ##################################
@login_required
def play_song_view(request, song_id):
    """
    deliver a song. better to say: "let nginx deliver the song"
    """

    song = Song.objects.get(id=song_id)
    # append "/music" , strip filesystem prefix (/media....)
    path = "/music" + song.path_orig[len(settings.MUSIC_PATH):]
    response = HttpResponse()
    response["Content-Type"] = ""
    response["X-Accel-Redirect"] = path.encode("utf-8")

    return response

@login_required
def play_view(request):
    """
    administrate song request. returns urls for audio player <source> tag and song info
    """
    song = None

    if request.method == "POST":
        user_status = helper.UserStatus(request)

        #ms = MusicSession.objects.get(user=request.user)
        source = request.POST.get('source')
        if "playlist" == source:
            playlist_id = request.POST.get("playlist_id")
            item_id     = request.POST.get("item_id")

            user_status.set("playing_source", "playlist")
            user_status.set("playing_playlist_id", playlist_id)
            user_status.set("playing_playlist_item_id", playlist_id)

            playlist = Playlist.objects.get(id=playlist_id)
            item     = PlaylistItem.objects.get(id=item_id)
            playlist.current_position = item.position
            playlist.save()

            song = item.song

            return song_info_response(song, playlist=playlist, item_id=item.id)

        elif "browse" == source:
            song_id = request.POST.get("song_id")

            user_status.set("playing_song_id", song_id)
            user_status.set("playing_source", "browse")

            song = Song.objects.get(id=song_id)

            return song_info_response(song)

        else:
            song_id = request.POST.get('song_id')

            user_status.set("playing_source", "collection")
            user_status.set("playing_song_id", song_id)

            song = Song.objects.get(id=song_id)

            return song_info_response(song)

    return HttpResponse("Only POST request implemented so far")

@login_required
def play_next_view(request):

    if request.method == "POST":

        #ms = MusicSession.objects.get(user=request.user)
        user_status = helper.UserStatus(request)
        song = None

        source = user_status.get("playing_source", "collection")

        if "playlist" == source:
            # attention: multiple songs with same song.id can be in playlist.items
            pl_id = user_status.get("playing_playlist_id", "")

            if "" == pl_id:
                # this could happen when library is empty
                return song_info_response(Song.objects.filter(user=request.user)[0:1])

            pl = Playlist.objects.get(id=pl_id)

            current_position = pl.current_position + 1
            if current_position <= len(pl.items.all()):
                pl.current_position = current_position
                pl.save()
                item = pl.items.get(position=current_position)
                song = item.song
            return song_info_response(song, playlist_id=pl.id, item_id=item.id)

        elif "browse" == source:
            songs = helper.search(request, browse=True)

        else:
            # assuming "collection" as source
            songs = helper.search(request)

        current_song_id = user_status.get("playing_song_id", "")

        if "" == current_song_id:
            # this could happen when library is empty
            return song_info_response(Song.objects.filter(user=request.user)[0:1])

        current_song = Song.objects.get(id=current_song_id, user=request.user)
        found = False
        song = None
        for s in songs:
            if found == True:
                song = s
                user_status.set("playing_song_id", str(song.pk))
                break
            if s == current_song:
                found = True
        return song_info_response(song)


    return song_info_response(song)


#######################      internals     ##################################

@login_required
@transaction.autocommit
def rescan_view(request):
    """
    on POST requests: starts rescan. If rescan in progress, return rescan status.
    on GET requests: return rescan status
    """

    col = Collection.objects.get(user=request.user)
    if request.method == "POST":
        if request.POST.get("cancel", False):
            col.scan_status = "idle"
            col.save()
            return HttpResponse(col.scan_status)

    if col.scan_status == "idle" or col.scan_status == "error" or col.scan_status == "":
        if request.method == "POST":
            col.scan_status = "started"
            col.save()
            helper.dbgprint("rescan request accepted from user", request.user)
            from music.tasks import rescan_task
            stat = rescan_task.delay(request.user.id)
            return HttpResponse("started")

    elif col.scan_status == "finished":
        col.scan_status = "idle"
        col.save()

    return HttpResponse(col.scan_status)

def song_info_response(song, playlist_id=None, item_id=None):

    if song == None:
        return HttpResponse("")

    if playlist_id and item_id:
        pass
    else:
        playlist_id = 0
        item_id = 0

    filename = os.path.split(song.path_orig)[-1]
    dbg_file_path = "/music" + song.path_orig[len(settings.MUSIC_PATH):]


    # Some null field checks
    try:
        artist = song.artist.name
    except AttributeError:
        artist = "Unknow"
    try:
        album = song.album.name
    except AttributeError:
        album = "Unknow"
    try:
        genre = song.genre.name
    except AttributeError:
        genre = "Unknow"

    song_info = {
            'playlist_id': playlist_id,
            'item_id':     item_id,

            'song_id':     song.id,
            'title':       song.title,
            'artist':      artist,
            'album':       album,
            'genre':       genre,
            'track':       song.track,
            'mime':        song.mime,
            'filename':    filename,
            'dbg_file_path': dbg_file_path,
            }
    response = HttpResponse(simplejson.dumps(song_info), mimetype='application/json')
    response['Cache-Control'] = 'no-cache'
    return response

def login_view(request):

    if request.method == "POST":

        username = request.POST['username']
        password = request.POST['password']

        form = auth.forms.AuthenticationForm(request.POST)
        if not form.is_valid:
            return render_to_response(
                    "registration/login.html",
                    locals(),
                    context_instance=RequestContext(request),
                    )

        user = auth.authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                auth.login(request, user)
                return HttpResponseRedirect(reverse("home"))
            else:
                return HttpResponse("Your account was disabled.")
        else:
            return HttpResponseRedirect(reverse("login_view"))

    form = auth.forms.AuthenticationForm()
    return render_to_response(
            "registration/login.html",
            locals(),
            context_instance=RequestContext(request),
            )

def logout_view(request):
    auth.logout(request)
    return HttpResponseRedirect(reverse('home'))

def get_filtered(request):
    """
    returns [songs, artists, albums] queries based on user's music session
    if .filter_show of music_session is False, returns [songs, None, None], with
    no respect to the preselected artists or albums

    .search_terms will be split on " " in terms and terms are treated with AND
    artists in .filter_artists will be treated with OR
    albums in .filter_albums will be treated with OR
    result of artists and albums in .filter_artists and .filter_albums will be treated with AND

    The returned artists and albums will contain only the ones based on .search_terms.
    albums will contain only the albums of the selected artists.
    """

    #music_session = MusicSession.objects.get(user=user)
    #terms = music_session.search_terms

    user_status = helper.UserStatus(request)
    terms = user_status.get("search_terms", "")

    songs = Song.objects.select_related().filter(user=request.user).order_by("artist__name", "album__name")


    if len(terms) > 0:
        term_list = terms.split(" ")

        songs = songs.filter(Q(artist__name__icontains=term_list[0]) | \
                                    Q(title__icontains=term_list[0]) | \
                                    Q(album__name__icontains=term_list[0]) | \
                                    Q(mime__icontains=term_list[0]))
        for term in term_list[1:]:
            songs = songs.filter(Q(artist__name__icontains=term) | \
                                 Q(title__icontains=term) | \
                                 Q(album__name__icontains=term) | \
                                 Q(mime__icontains=term))

        # show artists and albums only for the songs matched by .search_terms
        # TODO: this is not nice. Isn't it possible to build a querie? Attention:
        # songs can be many (>10000). So the query must be set up carefully.
# deprecated
#        if music_session.filter_show:
#            from itertools import groupby
#            artists = [ k for k, g in groupby(songs, lambda x: x.artist_set.all()[0:1].get())]
#            albums  = [k for k, g, in groupby(songs, lambda x: x.album_set.all()[0:1].get())]
#
#            # now apply filters for artists from the select boxes (using OR)
#            queries = [Q(artist__pk=artist.pk) for artist in music_session.filter_artists.all()]
#            if len(queries)>0:
#                query = queries.pop()
#                for q in queries:
#                    query |= q
#                songs = songs.filter(query)
#
#            # now apply filters for albums from the select boxes (using OR)
#            queries = [Q(album__pk=album.pk) for album in music_session.filter_albums.all()]
#            if len(queries)>0:
#                query = queries.pop()
#                for q in queries:
#                    query |= q
#                songs = songs.filter(query)
#        else:
#            artists = None
#            albums = None
#
#    else:
#        # For the filter view: the displayed artists and albums should contain
#        # all artists and albums the user has songs of
#        if music_session.filter_show:
#            artists = Artist.objects.select_related('songs').filter(songs__user=user).distinct()
#            albums  = Album.objects.select_related('songs').filter(songs__user=user).distinct()
#
#        else:
#            artists = None
#            albums = None
#
#    return [songs, artists, albums]
    return [songs, None, None]


def filter_songs(request, terms, artists=None, albums=None):
    """
    returns songs for user
    """

    if not terms == None:
        if not (type(terms) == unicode or type(terms) == str):
            helper.dbgprint("Invalid type for terms:", type(terms), terms)
            songs = Song.objects.filter(user=request.user)

        elif len(terms) == 0:
            # return all songs
            songs = Song.objects.filter(user=request.user)

        else:
            term_list = terms.split(" ")
            songs = Song.objects.filter(Q(artist__name__icontains=term_list[0]) | \
                                        Q(title__icontains=term_list[0]) | \
                                        Q(album__name__icontains=term_list[0]) | \
                                        Q(mime__icontains=term_list[0]), user=request.user)
            for term in term_list[1:]:
                songs = songs.filter(Q(artist__name__icontains=term) | \
                                     Q(title__icontains=term) | \
                                     Q(album__name__icontains=term) | \
                                     Q(mime__icontains=term), user=request.user)
                print("search terms left songs:", songs.count())
        if albums:
            # build a query for albums
            queries = [ Q(album__pk=pk) for pk in albums.keys()]
            query = queries.pop()
            for q in queries:
                query |= q
            songs = songs.filter(query)
            print("album left songs", songs.count())

        if artists:
            queries = [ Q(artist=a) for a in artists.keys()]
            query = queries.pop()
            for q in queries:
                query |= q
            songs = songs.filter(query)

    else:
        songs = []

    return songs
