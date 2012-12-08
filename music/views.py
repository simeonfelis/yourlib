from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseNotFound
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import simplejson
from django.db.models import Q
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError, PermissionDenied
from celery.result import AsyncResult

from music.models import Song, Artist, Album, Genre, Playlist, PlaylistItem, MusicSession, Collection, Upload, Download, SharePlaylist, SharePlaylistSubscription
from music.forms import UploadForm, BrowseSettingsColumnsForm
#from music.helper import dbgprint, UserStatus, user_status_defaults
from music import helper
from music import settings

import os, time
from Image import init

INITIAL_ITEMS_LOAD_COUNT = 200
SUBSEQUENT_ITEMS_LOAD_COUNT = 200

@login_required
def home_view(request):

    # Init user folder if not existent
    if not os.path.isdir(os.path.join(settings.MUSIC_PATH, request.user.username)):
        os.makedirs(os.path.join(settings.MUSIC_PATH, request.user.username))

    playlists = Playlist.objects.filter(user=request.user)
    # create playlists if not existent for user
    if 0 == len(playlists):
        print("Creating default playlist for user ", request.user)
        pl = Playlist(name="default", user=request.user, current_position=0)
        pl.save()
        playlists = Playlist.objects.filter(user=request.user)

    try:
        music_session = MusicSession.objects.get(user=request.user)
    except MusicSession.DoesNotExist:
        # create music session with status information if not yet exists
        music_session = MusicSession(
            status = helper.user_status_defaults,
            user=request.user,
            currently_playing='none',
            search_terms='',
            filter_show=False
        )
        music_session.save()

    user_status = helper.UserStatus(request)

    current_view = user_status.get("current_view", "collection")

    if "playlist" == current_view:
        current_view_playlist = user_status.get("current_view_playlist", 0)
        try:
            # make sure the playlist exists
            pl = Playlist.objects.get(id=current_view_playlist, user=request.user)
        except Playlist.DoesNotExist:
            # get any random one
            pl = Playlist.objects.get(request.user)

        playlist_id = pl.id

        return HttpResponseRedirect(reverse("playlist", kwargs={"playlist_id": playlist_id}))
        #cur_pos = music_session.current_playlist.current_position

        #current_item = music_session.current_playlist.items.get(position=cur_pos)

        # the following is needed to prefill player data
        #current_song = current_item.song
        #current_item_id = current_item.id
        #current_song_id = current_song.id
        #current_playlist_id = music_session.current_playlist.id

    else: #elif "collection" == current_view:
        return HttpResponseRedirect(reverse("collection"))
        #current_song = music_session.current_song
        #current_song_id = current_song.id
        #current_playlist_id = 0
        #current_item_id = 0

# TODO: deprecated
#    songs = helper.search(request)
#    songs_count = songs.count()
#    if len(songs) > INITIAL_ITEMS_LOAD_COUNT:
#        songs = songs[:INITIAL_ITEMS_LOAD_COUNT]
#
#    subscribed_playlists = SharePlaylist.objects.filter(subscribers=request.user)
#
#    return render_to_response(
#            'home.html',
#            locals(),
#            context_instance=RequestContext(request),
#            )

##################### collection ##########################

@login_required
def collection_view(request):
    global INITIAL_ITEMS_LOAD_COUNT
    global SUBSEQUENT_ITEMS_LOAD_COUNT

    user_status = helper.UserStatus(request)

    songs = helper.search(request)

    load_full_page = False
    if request.method == "POST":
        load_full_page = True
    else:
        if not "so_far" in request.GET.keys():
            load_full_page = True

    if load_full_page:
        if request.method == "POST":
            user_status.set("current_view", "collection")

        search_terms = user_status.get("collection_search_terms", "")

        songs_count = songs.count() # .count() instead of len(), because of slicing!
        songs = songs[:INITIAL_ITEMS_LOAD_COUNT]

        # sidebar data
        sidebar = {
            "playlists": Playlist.objects.filter(user=request.user),
            "subscribed_playlists": SharePlaylist.objects.filter(subscribers=request.user),
        }

        return render_to_response(
                "context_collection.html",
                locals(),
                context_instance=RequestContext(request),
                )
    else:
        # pagination
        so_far = int(request.GET.get("so_far", "0"))
        want   = int(request.GET.get("want", "%s" % SUBSEQUENT_ITEMS_LOAD_COUNT))
        songs = songs[so_far : so_far + want]

        return render_to_response(
                "collection_songs_li.html",
                locals(),
                context_instance=RequestContext(request),
                )



@login_required
def collection_search_view(request):

    global INITIAL_ITEMS_LOAD_COUNT

    search_terms = request.POST.get("search_terms", "")
    user_status = helper.UserStatus(request)

    if request.method == "POST":
        user_status.set("collection_search_terms", search_terms)

    else:
        search_terms = user_status.get("collection_search_terms", "")

    songs = helper.search(request)

    songs_count = songs.count() # use .count() instead of len() because of slicing!

    songs = songs[:INITIAL_ITEMS_LOAD_COUNT]

    # sidebar data
    sidebar = {
        "playlists": Playlist.objects.filter(user=request.user),
        "subscribed_playlists": SharePlaylist.objects.filter(subscribers=request.user),
    }

    return render_to_response(
            'context_collection.html',
            locals(),
            context_instance=RequestContext(request),
            )

@login_required
def collection_play_view(request):
    if request.method == "POST":

        try:
            song_id = int(request.POST.get("song_id", "0"))
        except ValueError:
            song_id = 0

        user_status = helper.UserStatus(request)
        user_status.set("current_source", "collection")
        user_status.set("current_song_id", song_id)

        return HttpResponseRedirect(reverse("play", kwargs={"play_id": repr(song_id)}))

    # GET requests: not supported
    return HttpResponse("Only POST requests allowed")

@login_required
def collection_settings_view(request):
    # TODO: collection_settings_view
    pass


# TODO: collection_songs_view deprecated
#@login_required
#def collection_songs_view(request):
#
#    so_far = int(request.POST.get("so_far", 0))
#
#    songs = helper.search(request)
#    songs_count = songs.count()
#
#    if songs_count > so_far+SUBSEQUENT_ITEMS_LOAD_COUNT:
#        songs = songs[so_far:so_far+SUBSEQUENT_ITEMS_LOAD_COUNT]
#    else:
#        songs = songs[so_far:]
#
#    return render_to_response(
#            "collection_songs_li.html",
#            locals(),
#            context_instance=RequestContext(request),
#            )


@login_required
def collection_browse_view(request):

    # reset selections
    user_status = helper.UserStatus(request)
    user_status.set("browse_selected_albums", [])
    user_status.set("browse_selected_artists", [])

    songs   = Song.objects.select_related().filter(user=request.user).order_by("artist__name", "album__name", "track")
    songs   = songs[:INITIAL_ITEMS_LOAD_COUNT]

    genres  = Genre.objects.filter(song__user=request.user).distinct().order_by("name", "name")
    genres  = genres[:INITIAL_ITEMS_LOAD_COUNT]

    artists = Artist.objects.filter(song__user=request.user).distinct().order_by("name")
    artists = artists[:INITIAL_ITEMS_LOAD_COUNT]

    albums  = Album.objects.filter(song__user=request.user).distinct().order_by("name")
    albums  = albums[:INITIAL_ITEMS_LOAD_COUNT]


    columns_display = user_status.get("browse_column_display", helper.DEFAULT_BROWSE_COLUMNS_AVAILABLE)

    # sidebar data
    sidebar = {
        "playlists": Playlist.objects.filter(user=request.user),
        "subscribed_playlists": SharePlaylist.objects.filter(subscribers=request.user),
    }

    return render_to_response(
            "context_browse.html",
            locals(),
            context_instance=RequestContext(request),
            )


@login_required
def settings_collection_browse_view(request):

    user_status = helper.UserStatus(request)
    columns = user_status.get("browse_column_display", helper.DEFAULT_BROWSE_COLUMNS_AVAILABLE)

    if request.method == "POST":
        column_form = BrowseSettingsColumnsForm(request.POST, prefix="column_selection")
        if column_form.is_valid():
            column_form.save(user_status)

    else:
        column_form = BrowseSettingsColumnsForm(columns=columns, prefix="column_selection")

    return render_to_response(
            "settings_collection_browse.html",
            locals(),
            context_instance=RequestContext(request),
            )


@login_required
def collection_browse_column_view(request, column):
#    On POST requests expects to set filter and returns full page
#    On GET requests containing parameter so_far, it will provide column
#    entries for pagination
#    Depending on column, returns subsequent column based on ordering in user_status
#
#    E.g. column order is: [genre, artist, album]:
#    If column is genre: returns list of artists, albums and songs.
#    If column is album: returns list of songs.
#
#    The returned lists are filtered by the selection of the items in column.
#    The item IDs have to be transmitted in the POST request in "items[]". The
#    selection will be stored in the user_status.


    user_status = helper.UserStatus(request)

    # consider 'column' as 'column_from'. This is more logical and easier to read (and used in templates)
    column_from = column

    # get IDs from selected column entries. They will be used as filter
    if request.method == "POST":
        items = request.POST.getlist('items[]', None)
    else:
        items = request.GET.getlist('items[]', None)

    # sanity check
    if not column_from in ["genre", "artist", "album"]:
        ret = HttpResponse("Unsupported column: '%s'" % column_from)
        ret.status_code = 400
        return ret

    # store filter
    user_status.set("browse_selected_%s" % column_from, items)

    # determine order number of column_from
    columns_display = user_status.get("browse_column_display", helper.DEFAULT_BROWSE_COLUMNS_AVAILABLE)
    column_from_order = 0 # avoid exception because of undefined variable
    for column_settings in columns_display:
        if column_settings["name"] == column_from:
            column_from_order = column_settings["order"]

    # Determine columns to render. Unset filter of later columns. Remember
    # filter of previous columns.
    # Create a list with correct order.
    columns_filter = []
    last_order = 1000
    for column_settings in columns_display:

        if column_settings["show"]:

            current_order  = column_settings["order"]
            name           = column_settings["name"]

            # clear selection of subsequent columns
            if current_order > column_from_order:
                user_status.set("browse_selected_%s" % name, [])
                selected = []
            else:
                selected = user_status.get("browse_selected_%s" % name, [])

            # fetch model references. Will be useful later
            if   name == "artist": model = Artist
            elif name == "album":  model = Album
            elif name == "genre":  model = Genre

            filter_item = {
                "name": name,           # the column name
                "selected": selected,
                "model": model,
            }

            if last_order < current_order:
                columns_filter.append(filter_item)
            else:
                columns_filter.insert(0, filter_item )

            last_order = current_order

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


#        if "genre" == column_from:
#            user_status.set("browse_selected_genres", items)
#
#        elif "artist" == column_from:
#            # store selected items
#            user_status.set("browse_selected_artists", items)
#
#            # Set the columns to be rendered by templates
#            #columns = ["album", "title"]
#            #albums, songs = helper.browse_column_album(request)
#            #albums = albums[:INITIAL_ITEMS_LOAD_COUNT]
#
#        elif "album" == column_from:
#            # store selected items
#            user_status.set("browse_selected_albums", items)
#
#            # Set the columns to be rendered by templates
#            #columns = ["title"]
#            #songs = helper.browse_column_title(request)
#
#        else:
#            return HttpResponse("Unsupported column: " + column_from)

#        songs = songs[:INITIAL_ITEMS_LOAD_COUNT]

    if len(queries_song):
        q_song = queries_song.pop()
        for q in queries_song:
            q_song |= q
        songs = Song.objects.filter(user=request.user).filter(q_song).distinct()
    else:
        songs = Song.objects.filter(user=request.user).distinct()

    # Build OR queries from all queries
    if len(queries_genre):
        q_genre = queries_genre.pop()
        for q in queries_genre:
            q_genre |= q
        genres = Genre.objects.filter(q_genre).filter(song__user=request.user).distinct()
    else:
        genres = Genre.objects.filter(song__user=request.user).distinct()

    if len(queries_artist):
        q_artist = queries_artist.pop()
        for q in queries_artist:
            q_artist |= q
        artists = Artist.objects.filter(q_artist).filter(song__user=request.user).distinct()
    else:
        artists = Artist.objects.filter(song__user=request.user).distinct()

    if len(queries_album):
        q_album = queries_album.pop()
        for q in queries_album:
            q_album |= q
        albums = Album.objects.filter(q_album).filter(song__user=request.user).distinct()
    else:
        albums = Album.objects.filter(song__user=request.user).distinct()


    return render_to_response(
            "context_browse.html",
            locals(),
            context_instance=RequestContext(request),
            )
    # pagination
    so_far = int(request.GET.get("so_far", "0"))
    want   = int(request.GET.get("want", "%s" % SUBSEQUENT_ITEMS_LOAD_COUNT))

    # column is the column which wants more items

    if "artist" == column:
        items = Artist.objects.filter(song__user = request.user).distinct()
    elif "album" == column:
        items, dump = helper.browse_column_album(request)
    elif "title" == column:
        items = helper.browse_column_title(request)

    items_count = items.count()
    items = items[so_far : so_far + want]

    if "artist" == column:
        artists = items
    elif "album" == column:
        albums = items
    elif "title" == column:
        songs = items
        return render_to_response(
                "collection_songs_li.html",
                locals(),
                context_instance=RequestContext(request),
                )


    return render_to_response(
            "browse_column_li.html",
            locals(),
            context_instance=RequestContext(request),
            )


# TODO: deprecated collection_browse_more_view
#@login_required
#def collection_browse_more_view(request, column):
#    """
#    Returns more items for `column` based on selection.
#    Selection should be stored in user_settings previously.
#    If nothing is selected, returns all items of list.
#    """
#
#    so_far = int(request.POST.get("so_far"))
#
#    if "artist" == column:
#        items = Artist.objects.filter(song__user = request.user).distinct()
#    elif "album" == column:
#        items, dump = helper.browse_column_album(request)
#    elif "title" == column:
#        items = helper.browse_column_title(request)
#
#    items_count = items.count()
#
#    if items_count > so_far+SUBSEQUENT_ITEMS_LOAD_COUNT:
#        items = items[so_far:so_far+SUBSEQUENT_ITEMS_LOAD_COUNT]
#    else:
#        items = items[so_far:]
#
#    if len(items) == 0:
#        return HttpResponse("nomoreresults")
#
#
#    if "artist" == column:
#        artists = items
#    elif "album" == column:
#        albums = items
#    elif "title" == column:
#        songs = items
#
#
#    return render_to_response(
#            "browse_column_li.html",
#            locals(),
#            context_instance=RequestContext(request),
#            )

def show_context_download(request):
    downloads = Download.objects.get(user=request.user)
    return render_to_response(
            "context_download.html",
            locals(),
            context_instance=RequestContext(request),
            )

# TODO: deprecated?
#def show_context_upload(request):
#    uploads = Upload.objects.filter(user=request.user)
#
#    form = UploadForm(request.POST)
#    return render_to_response(
#            "context_upload.html",
#            locals(),
#            context_instance=RequestContext(request),
#            )

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

# TODO: show_context_playlist deprecated?
#def show_context_playlist(request):
#    if request.method == "POST":
#        playlist_id = request.POST.get('playlist_id')
#        playlist = Playlist.objects.get(id=playlist_id)
#    else:
#        playlist = Playlist.objects.get(user=request.user)
#
#    return render_to_response(
#            "context_playlist_deprecated.html",
#            locals(),
#            context_instance=RequestContext(request),
#            )

@login_required
def shares_view(request):
    """
    Shows overview of shares and subscriptions
    """
    if request.method == "POST":
        pass

    # sidebar data
    sidebar = {
        "playlists": Playlist.objects.filter(user=request.user),
        "subscribed_playlists": SharePlaylist.objects.filter(subscribers=request.user),
    }

    #shares content
    shared_playlists = SharePlaylist.objects.filter(playlist__user=request.user)
    subscribed_playlists = SharePlaylist.objects.filter(subscribers=request.user)

    return render_to_response(
            "context_shares.html",
            locals(),
            context_instance=RequestContext(request),
            )

@login_required
def shares_playlist_view(request, playlist_id):

    if request.method == "POST":
        pass

    playlist = Playlist.objects.get(id=playlist_id)

    # check if visitor is really allowed to see the playlist
    subscribed_playlists = SharePlaylist.objects.filter(subscribers=request.user)
    if not subscribed_playlists.filter(playlist=playlist).count():
        raise PermissionDenied

    # sidebar data
    sidebar = {
        "playlists": Playlist.objects.filter(user=request.user),
        "subscribed_playlists": subscribed_playlists,
    }

    shared_by = playlist.user

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
def upload_view(request):

    user_status = helper.UserStatus(request)
    #user_status.set("current_context", "upload")


    uploads = Upload.objects.filter(user=request.user)

    form = UploadForm(request.POST)

    # sidebar data
    sidebar = {
        "playlists": Playlist.objects.filter(user=request.user),
        "subscribed_playlists": SharePlaylist.objects.filter(subscribers=request.user),
    }

    return render_to_response(
            "context_upload.html",
            locals(),
            context_instance=RequestContext(request),
            )


#@csrf_exempt
@login_required
def upload_file_view(request):
    if request.method == 'POST':
        if request.FILES == None:
            return HttpResponse("No files received")

        upfile = request.FILES[u'file']

        #################################  copying ################################
#        helper.dbgprint("Entering status copying")
#        step_status = 0
#
        userUploadStatus = Upload(user=request.user, step="received", step_status=0)
        userUploadStatus.save()
#
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

        # django docs say: don't do that! furthermore the file is still open!
        # but handling chunks can take ages on large uploads (like 2Gig)
        import shutil
        shutil.move(upfile.file.name, useruppath)
#
#        helper.dbgprint("Copy-to location:", useruppath, type(useruppath))
#
#        # now put the upload content to the user's location
#        step_status = 0
#        processed = 0
#        amount = upfile.size
#        helper.dbgprint("Chunks:", amount)
#        old_status = 0
#        with open(useruppath, 'wb+') as destination:
#            for chunk in upfile.chunks():
#                processed += upfile.DEFAULT_CHUNK_SIZE
#                destination.write(chunk)
#                step_status = int(processed*100/amount)
#                if (old_status < step_status) and (step_status % 2 == 0):
#                    helper.dbgprint("Chunks copied:", step_status, "%")
#                    userUploadStatus.step_status = step_status
#                    userUploadStatus.save()
#                    old_status = step_status
#            destination.close()
#        helper.dbgprint("Uploaded file written to", useruppath)

        # so here the upload is done and can be analyzed
        from music.tasks import upload_done
        #stat = upload_done.delay(useruppath, userupdir, userUploadStatus.id)
        stat = upload_done.delay(user_id=request.user.id, upload_status_id=userUploadStatus.id, uploaded_file_path=useruppath)

        time.sleep(3) #give celery 3 second to accept the task
        res = AsyncResult(stat.task_id).state
        if res == "PENDING":
            userUploadStatus.step = "pending"
            userUploadStatus.save()

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
def upload_status_view(request):
    uploads = Upload.objects.filter(user=request.user)
    return render_to_response(
            'upload_status.html',
            locals(),
            context_instance=RequestContext(request),
            )

@login_required
def upload_clearpending_view(request):
    to_clear = Upload.objects.filter(user=request.user, step__icontains="pending").delete()

    uploads = Upload.objects.filter(user=request.user)

    return render_to_response(
            'upload_status.html',
            locals(),
            context_instance=RequestContext(request),
            )

#############################      playlist stuff     ##################################

@login_required
def playlist_view(request, playlist_id):

    try:
        playlist_id = int(playlist_id)
    except ValueError:
        playlist_id = 0

    if request.method == "POST":
        user_status = helper.UserStatus(request)
        user_status.set("current_view", "playlist")
        user_status.set("current_view_playlist", playlist_id)

    playlist = Playlist.objects.get(id=playlist_id)

    if playlist.user != request.user:
        raise PermissionDenied

    # sidebar data
    sidebar = {
        "playlists": Playlist.objects.filter(user=request.user),
        "subscribed_playlists": SharePlaylist.objects.filter(subscribers=request.user),
    }

    return render_to_response(
            "context_playlist.html",
            locals(),
            context_instance=RequestContext(request),
            )

# TODO: sidebar_playlists_view deprecated?
#@login_required
#def sidebar_playlists_view(request):
#    """
#    return list of all playlists
#    """
#    playlists = Playlist.objects.filter(user=request.user)
#    return render_to_response(
#            'sidebar_playlists.html',
#            locals(),
#            context_instance=RequestContext(request),
#            )

# TODO: playlists_view deprecated?
#@login_required
#def playlists_view(request):
#    playlists = Playlist.objects.filter(user=request.user)
#
#    return render_to_response(
#            'context_playlists.html',
#            locals(),
#            context_instance=RequestContext(request),
#            )

@login_required
def playlist_create_view(request):

    if request.method == "POST":
        name = request.POST.get('playlist_name')
        if not len(name) > 0:
            raise Exception("playlist name invalid: " + str(name))
        # check if same name exists for user
        try:
            playlist = Playlist.objects.get(user=request.user, name=name)
        except Playlist.DoesNotExist:

            playlist = Playlist(name=name, user=request.user, current_position=0)
            playlist.save()

        # sidebar data
        sidebar = {
            "playlists": Playlist.objects.filter(user=request.user),
            "subscribed_playlists": SharePlaylist.objects.filter(subscribers=request.user),
        }

        #return HttpResponseRedirect(reverse("playlist", kwargs={"playlist_id": playlist.id}))

        return render_to_response(
                "context_playlist.html",
                locals(),
                context_instance=RequestContext(request),
                )

    return HttpResponse("Only POST request allowed")

@login_required
def playlist_delete_view(request, playlist_id):
    if request.method == "POST":

        playlist = Playlist.objects.get(id=playlist_id)

        if playlist.user != request.user:
            raise PermissionDenied

        if playlist.name == "default":
            return HttpResponse("You can't delete the default playlist. it should stay.") # TODO: make a nice message

        playlist.delete()

        # return the first playlist of user
        [playlist] = Playlist.objects.filter(user=request.user)[0:1]

        # sidebar data
        sidebar = {
            "playlists": Playlist.objects.filter(user=request.user),
            "subscribed_playlists": SharePlaylist.objects.filter(subscribers=request.user),
        }

        return render_to_response(
                "context_playlist.html",
                locals(),
                context_instance=RequestContext(request),
                )

    return HttpResponse("Only POST requests allowd")

@login_required
def playlist_append_view(request, playlist_id):
    if request.method == "POST":
        item_id      = request.POST.get("item_id", "0")
        source       = request.POST.get("source")

        playlist = Playlist.objects.get(id=playlist_id)

        if "song" == source:
            songs = [Song.objects.get(user=request.user, id=item_id)]
        elif "collection" == source:
            songs = [Song.objects.get(user=request.user, id=item_id)]
        elif "artist" == source:
            songs = Song.objects.filter(user=request.user, artist__id=item_id)
        elif "album" == source:
            songs = Song.objects.filter(user=request.user, album__id=item_id)
        elif "title" == source:
            songs = Song.objects.filter(user=request.user, id=item_id)
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

        #playlists = Playlist.objects.filter(user=request.user)

        playlist_info = {
            "playlist_id": playlist.id,
            "count": playlist.items.all().count(),
        }

        response = HttpResponse(simplejson.dumps(playlist_info), mimetype='application/json')

        return response

        #return render_to_response(
        #        'sidebar_playlists.html',
        #        locals(),
        #        context_instance=RequestContext(request),
        #        )

    # Do not change anything on GET requests
    playlists = Playlist.objects.filter(user=request.user)
    return render_to_response(
            'context_playlist.html',
            locals(),
            context_instance=RequestContext(request),
            )

@login_required
def playlist_remove_item_view(request, playlist_id):

    playlist = Playlist.objects.get(id=playlist_id, user=request.user)

    if request.method == "POST":
        item_id = request.POST.get("item_id", "0")
        item = PlaylistItem.objects.get(id=item_id)
        position = item.position
        item.delete()
        # correct positions of all following items
        # TODO: this will be slow on large playlists, if item with low position number is removed
        for item in playlist.items.all().filter(position__gt=position):
            item.position = item.position-1
            item.save()

        # refetch playlist
        playlist = Playlist.objects.get(id=playlist_id, user=request.user)

    # Do not change anything on GET requests

    # sidebar data
    sidebar = {
        "playlists": Playlist.objects.filter(user=request.user),
        "subscribed_playlists": SharePlaylist.objects.filter(subscribers=request.user),
    }

    return render_to_response(
            'context_playlist.html',
            locals(),
            context_instance=RequestContext(request),
            )

@login_required
@transaction.autocommit
def playlist_reorder_view(request, playlist_id):
    # reorder algorithm was a saturday afternoon work. althoug sometimes slow,
    # the power of python made it beautiful. read it carefully, as it respects
    # the case if an item was moved to the very top (item_previous_id = "0") by
    # its cool queries (Q). also, item_moved_position is the original value,
    # but item_moved.position is going to be the new value

    playlist = Playlist.objects.get(user=request.user, id=playlist_id)

    if request.method == "POST":

        item_id             = request.POST.get("item_id", "0")
        item_previous_id    = request.POST.get("item_previous_id", "0")

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

    # sidebar data
    sidebar = {
        "playlists": Playlist.objects.filter(user=request.user),
        "subscribed_playlists": SharePlaylist.objects.filter(subscribers=request.user),
    }


    return render_to_response(
            'context_playlist.html',
            locals(),
            context_instance=RequestContext(request),
            )

@login_required
def playlist_share_view(request, playlist_id):

    if request.method == "POST":
        username = request.POST.get("username", "")

        if request.user.username == username:
            return HttpResponse("Don' share playlists to yourself")

        try:
            subscriber = User.objects.get(username=username)
        except User.DoesNotExist:
            return HttpResponseNotFound("User not found")

        playlist = Playlist.objects.get(id=playlist_id)

        if playlist.user != request.user:
            raise PermissionDenied

        # check if playlist is already shared
        try:

            share_playlist = SharePlaylist.objects.get(playlist=playlist)

            if subscriber in share_playlist.subscribers.all():
                return HttpResponse("User already subscribed")

        except SharePlaylist.DoesNotExist:
            share_playlist = SharePlaylist(playlist = playlist)
            share_playlist.save()

        # create share relation information
        subscription = SharePlaylistSubscription(
            share = share_playlist,
            subscriber = subscriber,
        )
        subscription.save()

    return HttpResponseRedirect(reverse("shares"))



@login_required
def playlist_unshare_view(request, playlist_id):

    if request.method == "POST":
        unshare_playlist = request.POST.get("unshare_playlist", False)

        playlist = Playlist.objects.get(id=playlist_id)

        share_playlist = SharePlaylist.objects.get(playlist=playlist, playlist__user=request.user)

        if unshare_playlist:
            share_playlist.subscribers.clear()

        else:
            subscriber_id = request.POST.get("subscriber_id", "0")

            subscription = SharePlaylistSubscription.objects.get(
                share = share_playlist,
                subscriber__id = subscriber_id
            )

            subscription.delete()

        # delete share when no subscribers left
        if not share_playlist.subscribers.all().count():
            share_playlist.delete()

        return HttpResponse("success")


def playlist_play_view(request, playlist_id):

    if request.method == "POST":

        try:
            item_id = int(request.POST.get("item_id", "0"))
            playlist_id = int(playlist_id)
        except ValueError:
            item_id = 0
            playlist_id = 0

        user_status = helper.UserStatus(request)
        user_status.set("current_source", "playlist")
        user_status.set("current_playlist_id", playlist_id)
        user_status.set("current_item_id", item_id)

        return HttpResponseRedirect(reverse("play", kwargs={"play_id": repr(item_id)}))

    else:
        return HttpResponse("GET request not support")

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
def play_view(request, play_id):
    if request.method == "POST":
        pass
    else:

        user_status = helper.UserStatus(request)
        source = user_status.get("current_source", "collection")

        if "collection" == source:
            song_id = play_id
            try:
                song = Song.objects.get(id=song_id, user=request.user)
            except Song.DoesNotExist:
                raise PermissionDenied

            return song_info_response(song, source="collection")

        elif "playlist" == source:
            item_id = play_id
            playlist_id = user_status.get("current_playlist_id", 0)
            playlist = Playlist.objects.get(id=playlist_id)
            if request.user != playlist.user:
                # check if visitor is allowed to see the playlist
                subscribed_playlists = SharePlaylist.objects.filter(subscribers=request.user)
                if not subscribed_playlists.filter(playlist=playlist).count():
                    raise PermissionDenied

            song = playlist.items.get(id=item_id).song

            item = PlaylistItem.objects.get(id=item_id)

            return song_info_response(song, playlist_id=playlist.id, item_id=item.id, source=source)


# TODO: play_view deprecated
#@login_required
#def play_view(request):
#    """
#    administrate song request. returns urls for audio player <source> tag and song info
#    """
#
#    song = None
#
#    if request.method == "POST":
#        user_status = helper.UserStatus(request)
#
#        source = request.POST.get('source')
#        if "shared_playlist" == source:
#            playlist_id = request.POST.get("playlist_id")
#            item_id     = request.POST.get("item_id")
#
#            playlist = Playlist.objects.get(id=playlist_id)
#            item     = PlaylistItem.objects.get(id=item_id)
#
#            # check if visitor is allowed to see the playlist
#            subscribed_playlists = SharePlaylist.objects.filter(subscribers=request.user)
#            if not subscribed_playlists.filter(playlist=playlist).count():
#                raise PermissionDenied
#
#            user_status.set("playing_source", "playlist")
#            user_status.set("playing_playlist_id", playlist_id)
#            user_status.set("playing_playlist_item_id", item_id)
#
#            song = item.song
#
#            return song_info_response(song, playlist_id=playlist.id, item_id=item.id, source=source)
#
#
#        elif "playlist" == source:
#            playlist_id = request.POST.get("playlist_id")
#            item_id     = request.POST.get("item_id")
#
#            playlist = Playlist.objects.get(id=playlist_id, user=request.user)
#            item     = PlaylistItem.objects.get(id=item_id)
#
#            # check if visitor is allowed to see the playlist
#            subscribed_playlists = SharePlaylist.objects.filter(subscribers=request.user)
#            if not subscribed_playlists.filter(playlist=playlist).count():
#                raise PermissionDenied
#
#            user_status.set("playing_source", "playlist")
#            user_status.set("playing_playlist_id", playlist_id)
#            user_status.set("playing_playlist_item_id", item_id)
#
#            playlist.current_position = item.position
#            playlist.save()
#
#            song = item.song
#
#            return song_info_response(song, playlist_id=playlist.id, item_id=item.id, source=source)
#
#        elif "browse" == source:
#            song_id = request.POST.get("song_id")
#            song = Song.objects.get(id=song_id, user=request.user)
#
#            user_status.set("playing_song_id", song_id)
#            user_status.set("playing_source", "browse")
#
#            return song_info_response(song, source=source)
#
#        else:
#            song_id = request.POST.get('song_id')
#            song = Song.objects.get(id=song_id, user=request.user)
#
#            user_status.set("playing_source", "collection")
#            user_status.set("playing_song_id", song_id)
#
#            return song_info_response(song, source="collection")
#
#    return HttpResponse("Only POST request implemented so far")

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
                return song_info_response(Song.objects.filter(user=request.user)[0:1], source=source)

            pl = Playlist.objects.get(id=pl_id)

            current_position = pl.current_position + 1
            if current_position <= len(pl.items.all()):
                pl.current_position = current_position
                pl.save()
                item = pl.items.get(position=current_position)
                song = item.song
            return song_info_response(song, playlist_id=pl.id, item_id=item.id, source=source)

        elif "browse" == source:
            songs = helper.search(request, browse=True)

        else:
            # assuming "collection" as source
            source = "collection"
            songs = helper.search(request)

        current_song_id = user_status.get("playing_song_id", "")

        if "" == current_song_id:
            # this could happen when library is empty
            return song_info_response(Song.objects.filter(user=request.user)[0:1], source=source)

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
        return song_info_response(song, source=source)


    return HttpResponse("GET request not implemented")


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

def song_info_response(song, playlist_id=None, item_id=None, source=""):

    if song == None:
        return HttpResponse("No song")

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
            'year':        song.year,
            'length':      song.length,
            'track':       song.track,
            'mime':        song.mime,
            'source':      source,
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

    songs = Song.objects.select_related().filter(user=request.user).order_by("artist__name", "album__name", "track")


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

@login_required
def username_validation_view(request):

    result = False

    if request.method == "GET":
        username = request.GET.get("username", "")
        try:
            User.objects.get(username=username)
            result = True
        except User.DoesNotExist:
            pass

    result = {
        "exists": result
    }

    response = HttpResponse(simplejson.dumps(result), mimetype='application/json')
    return HttpResponse(response)

