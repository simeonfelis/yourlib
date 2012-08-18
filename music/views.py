from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.utils import simplejson
from django.conf import settings
from django.db.models import Q
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt

from music.models import Song, Artist, Album, Playlist, PlaylistItem, MusicSession, Collection, Upload, Download
from music.forms import UploadForm
from music.helper import dbgprint

import os


@login_required
@transaction.autocommit
def home(request):

    if request.user.is_authenticated():
        if not os.path.isdir(os.path.join(settings.MUSIC_PATH, request.user.username)):
            os.makedirs(os.path.join(settings.MUSIC_PATH, request.user.username))
        playlists = Playlist.objects.filter(user=request.user)
        # create playlists if not existent for user
        if 0 == len(playlists):
            dbgprint("Creating default playlist for user ", request.user)
            pl = Playlist(name="default", user=request.user, current_position=0)
            pl.save()
            playlists = Playlist.objects.filter(user=request.user)

        # current status
        try:
            music_session = MusicSession.objects.get(user=request.user)
        except MusicSession.DoesNotExist:
            dbgprint("Creating music session for user ", request.user)
            music_session = MusicSession(user=request.user, currently_playing='none', search_terms='', filter_show=False)
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

        songs = filter_songs(request, terms=music_session.search_terms)
        songs_count = songs.count()
        if len(songs) > 50:
            songs = songs[:50]

    return render_to_response(
            'home.html',
            locals(),
            context_instance=RequestContext(request),
            )

@login_required
@transaction.autocommit
def context(request, selection):

    music_session = MusicSession.objects.get(user=request.user)

    if selection == "download":
        if request.method == "POST":
            music_session.context = "download"
            music_session.save()
        downloads = Download.objects.get(user=request.user)
        return render_to_response(
                "context_download.html",
                locals(),
                context_instance=RequestContext(request),
                )

    elif selection == "upload":
        if request.method == "POST":
            music_session.context = "upload"
            music_session.save()

            uploads = Upload.objects.filter(user=request.user)

            form = UploadForm(request.POST)
            return render_to_response(
                    "context_upload.html",
                    locals(),
                    context_instance=RequestContext(request),
                    )

    elif selection == "collection":
        playlists = Playlist.objects.filter(user=request.user)

        if request.method == "POST":
            # store context view on POST
            music_session.context = "collection"
            music_session.save()

            songs = filter_songs(request, terms=music_session.search_terms)
            songs_count = songs.count()
            if len(songs) > 50:
                songs = songs[:50]
            albums = Album.objects.filter(songs__user=request.user).distinct()
            artists = Artist.objects.filter(songs__user=request.user).distinct()
            for term in music_session.search_terms.split(" "):
                albums = albums.filter(name__contains=term)
                artists = artists.filter(name__contains=term)
            return render_to_response(
                    "context_collection.html",
                    locals(),
                    context_instance=RequestContext(request),
                    )
        # GET request collection
        begin = int(request.GET.get('begin'), 0)
        howmany = 50
        songs = filter_songs(request, terms=music_session.search_terms)
        available = len(songs)
        if begin < available:
            if begin+howmany < available:
                songs = songs[begin:begin+howmany]
            else:
                songs = songs[begin:available]
        else:
            return HttpResponse("")

        return render_to_response(
                "collection_songs_li.html",
                locals(),
                context_instance=RequestContext(request),
                )

    elif selection == "filter":
        filter_show = request.POST.get("filter_show", "false")
        if filter_show == "false":
            filter_show = False
        else:
            filter_show = True
        music_session.filter_show = filter_show

        if filter_show:
            terms = music_session.search_terms.split(" ")
            artists = Artist.objects.filter(songs__user=request.user).distinct()
            for term in terms:
                artists = artists.filter(name__contains=term)
            albums = Album.objects.filter(songs__user=request.user).distinct()
            for term in terms:
                albums = albums.filter(name__contains=term)
        else:
            artists = None
            albums = None

        music_session.save()
        return render_to_response("collection_filter.html",
                locals(),
                context_instance=RequestContext(request),
                )

    elif selection == "playlist":
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

    return HttpResponse("")

#############################      upload     ##################################

@login_required
@csrf_exempt
@transaction.autocommit
def upload(request):
    if request.method == 'POST':
        if request.FILES == None:
            return HttpResponse("No files received")

        upfile = request.FILES[u'file']

        #################################  copying ################################
        dbgprint("Entering status copying")
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

        dbgprint("Copy-to location:", useruppath, type(useruppath))

        # now put the upload content to the user's location
        step_status = 0
        processed = 0
        amount = upfile.size
        dbgprint("Chunks:", amount)
        old_status = 0
        with open(useruppath, 'wb+') as destination:
            for chunk in upfile.chunks():
                processed += upfile.DEFAULT_CHUNK_SIZE
                destination.write(chunk)
                step_status = int(processed*100/amount)
                if (old_status < step_status) and (step_status % 2 == 0):
                    dbgprint("Chunks copied:", step_status, "%")
                    userUploadStatus.step_status = step_status
                    userUploadStatus.save()
                    old_status = step_status
            destination.close()
        dbgprint("Uploaded file written to", useruppath)

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
@transaction.autocommit
def filter(request, what):
    music_session = MusicSession.objects.get(user=request.user)
    if request.method == "POST":
        if what == "albums":
            album_ids = request.POST.getlist('albums[]', [])
            albums = Album.objects.in_bulk(album_ids)
#            ms.filter_albums.clear()
#            ms.filter_albums.add(albums)
            songs = filter_songs(request, terms=music_session.search_terms, albums=albums)
        elif what == "artists":
            artist_ids = request.POST.getlist('artists[]', [])
            artists = Artist.objects.in_bulk(artist_ids)
#            ms.filter_artists.clear()
#            ms.filter_artists.add(artists)
            songs = filter_songs(request, terms=music_session.search_terms, artists=artists)

        albums = Album.objects.filter(songs__user=request.user).distinct()
        artists = Artist.objects.filter(songs__user=request.user).distinct()
        for term in music_session.search_terms.split(" "):
            albums = albums.filter(name__contains=term)
            artists = artists.filter(name__contains=term)
        return render_to_response("collection_songs.html",locals())

@login_required
@transaction.autocommit
def search(request):

    if request.method == "POST":

        playlists = Playlist.objects.filter(user=request.user)
        music_session = MusicSession.objects.get(user=request.user)

        if 'terms' in request.POST:
            terms = request.POST.get('terms', '')
            music_session.search_terms = terms
            music_session.save()

            songs = filter_songs(request, terms=terms)
            songs_count = songs.count()
            if len(songs) > 50:
                songs = songs[:50]
            print "returning", len(songs), "search results"
            albums = Album.objects.filter(songs__user=request.user).distinct()
            artists = Artist.objects.filter(songs__user=request.user).distinct()
            for term in music_session.search_terms.split(" "):
                albums = albums.filter(name__contains=term)
                artists = artists.filter(name__contains=term)
            return render_to_response(
                    'collection_songs.html',
                    locals(),
                    context_instance=RequestContext(request),
                    )

    # return nothing on GET requests
    return HttpResponse("")

#############################      playlist stuff     ##################################

@login_required
def playlists(request):
    """
    return all playlists, e.g. for sidebar
    """
    playlists = Playlist.objects.filter(user=request.user)
    return render_to_response(
            'playlists.html',
            locals(),
            context_instance=RequestContext(request),
            )

@login_required
@transaction.autocommit
def playlist_create(request):
    if request.method == "POST":
        name = request.POST.get('playlist_name')
        if not len(name) > 0:
            raise Exception("playlist name invalid: " + str(name))
        playlist = Playlist(name=name, user=request.user, current_position=0)
        playlist.save()
        playlists = Playlist.objects.filter(user=request.user)

        return render_to_response(
                "playlists.html",
                locals(),
                context_instance=RequestContext(request),
                )

    return HttpResponse("")

@login_required
@transaction.autocommit
def playlist_delete(request):
    if request.method == "POST":

        playlist_id = request.POST.get('playlist_id')
        playlist = Playlist.objects.get(id=playlist_id)

        if playlist.name == "default":
            raise Exception("You can't delete the default playlist. it should stay.")

        playlist.delete()

        # return the first playlist from user
        playlist = Playlist.objects.filter(user=request.user)[0]

        return render_to_response(
                "context_playlist.html",
                locals(),
                context_instance=RequestContext(request),
                )

    return HttpResponse("")

@login_required
@transaction.autocommit
def playlist_append(request):
    if request.method == "POST":
        playlist_id = request.POST.get('playlist_id')
        song_id = request.POST.get('song_id')

        song = Song.objects.get(id=song_id)
        playlist = Playlist.objects.get(id=playlist_id)

        item = PlaylistItem(
                song = song,
                position = 1 + len(playlist.items.all())
                )

        item.save()
        playlist.items.add(item)
        playlist.save()
        playlists = Playlist.objects.filter(user=request.user)
        return render_to_response(
                'playlists.html',
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
@transaction.autocommit
def playlist_remove_item(request, playlist_id, item_id):

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
def playlist_reorder(request):
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
def play_song(request, song_id):
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
@transaction.autocommit
def play(request):
    """
    administrate song request. returns urls for audio player <source> tag and song info
    """
    song = None
    if request.method == "POST":
        ms = MusicSession.objects.get(user=request.user)
        song_id = request.POST.get('song_id')
        song = Song.objects.get(id=song_id)
        source = request.POST.get('source')

        if "collection" == source:
            ms.currently_playing = "collection"
            ms.current_song = song
            ms.save()
            return song_info_response(song)

        elif "playlist" == source:
            playlist = Playlist.objects.get(id=request.POST.get('playlist_id'))
            item = PlaylistItem.objects.get(id=request.POST.get('item_id'))
            playlist.current_position = item.position
            playlist.save()

            ms.currently_playing = "playlist"
            ms.current_playlist = playlist
            ms.save()
            return song_info_response(song, playlist_id=playlist.id, item_id=item.id)

    return song_info_response(song)

@login_required
@transaction.autocommit
def play_next(request):

    if request.method == "POST":

        ms = MusicSession.objects.get(user=request.user)
        song = None

        if "collection" == ms.currently_playing:
            # determin next song based on last search term
            # songs are unique in a collection or a filtered collection
            songs = filter_songs(request, terms=ms.search_terms)
            current_song = ms.current_song
            found = False
            song = None
            for s in songs:
                if found == True:
                    song = s
                    ms.current_song = s
                    ms.save()
                    break
                if s == current_song:
                    found = True
            return song_info_response(song)

        elif "playlist" == ms.currently_playing:
            # attention: multiple songs with same song.id can be in playlist.items
            pl = ms.current_playlist
            current_position = pl.current_position + 1
            if current_position <= len(pl.items.all()):
                pl.current_position = current_position
                pl.save()
                item = pl.items.get(position=current_position)
                song = item.song
            return song_info_response(song, playlist_id=pl.id, item_id=item.id)

    return song_info_response(song)


#######################      internals     ##################################

@login_required
@transaction.autocommit
def rescan(request):
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
            dbgprint("rescan request accepted from user", request.user)
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
    song_info = {
            'playlist_id': playlist_id,
            'item_id':     item_id,

            'song_id':     song.id,
            'title':       song.title,
            'artist':      song.artist,
            'album':       song.album,
            'track':       song.track,
            'mime':        song.mime,
            'filename':    filename,
            'dbg_file_path': dbg_file_path,
            }
    response = HttpResponse(simplejson.dumps(song_info), mimetype='application/json')
    response['Cache-Control'] = 'no-cache'
    return response

def login(request):
    return HttpResponse("Hi")

def filter_songs(request, terms=None, artists=None, albums=None):

    dbgprint("search: ", terms)

    if not terms == None:
        if not (type(terms) == unicode or type(terms) == str):
            dbgprint("Invalid type for terms:", type(terms), terms)
            songs = Song.objects.filter(user=request.user)

        elif len(terms) == 0:
            # return all songs
            songs = Song.objects.filter(user=request.user)

        else:
            term_list = terms.split(" ")
            songs = Song.objects.filter(Q(artist__name__contains=term_list[0]) | \
                                        Q(title__contains=term_list[0]) | \
                                        Q(album__name__contains=term_list[0]) | \
                                        Q(mime__contains=term_list[0]), user=request.user)
            for term in term_list[1:]:
                songs = songs.filter(Q(artist__name__contains=term) | \
                                     Q(title__contains=term) | \
                                     Q(album__name__contains=term) | \
                                     Q(mime__contains=term), user=request.user)
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
