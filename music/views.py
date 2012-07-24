from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.utils import simplejson
from django.utils.timezone import utc
from django.conf import settings
from django.db.models import Q

from music.models import Song, Playlist, PlaylistItem, MusicSession, Collection
from music.signals import rescan_start
from music.helper import dbgprint

import os, datetime, time

@login_required
def home(request):

    if request.user.is_authenticated():
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
            music_session = MusicSession(user=request.user, currently_playing='none', search_terms='')
            music_session.save()

        # create collection if not existent
        try:
            collection = Collection.objects.get(user=request.user)
        except Collection.DoesNotExist:
            collection = Collection(user=request.user, scan_status="idle")
            collection.save()


        songs = filter_songs(request, terms=music_session.search_terms)
        # not stable
        #if len(music_session.search_terms) > 0:
        #    artists = get_artists(request, songs)
        #else:
        #    # all artists
        #    artists = get_artists(request, None)

    return render_to_response(
            'home.html',
            locals(),
            context_instance=RequestContext(request),
            )

@login_required
def context(request, selection):
    if request.method == "POST":
        music_session = MusicSession.objects.get(user=request.user)
        if selection == "collection":

            music_session.context = "collection"
            music_session.save()
            playlists = Playlist.objects.filter(user=request.user)

            songs = filter_songs(request, terms=music_session.search_terms)

            return render_to_response(
                    "context_collection.html",
                    locals(),
                    context_instance=RequestContext(request),
                    )

        elif selection == "playlist":
            playlist_id = request.POST.get('playlist_id')
            playlist = Playlist.objects.get(id=playlist_id)
            return render_to_response(
                    "context_playlist.html",
                    locals(),
                    context_instance=RequestContext(request),
                    )

    return HttpResponse("")

@login_required
def search(request):

    if request.method == "POST":

        playlists = Playlist.objects.filter(user=request.user)
        ms = MusicSession.objects.get(user=request.user)

        if 'terms' in request.POST:
            terms = request.POST.get('terms')
            ms.search_terms = terms
            ms.save()

            songs = filter_songs(request, terms=terms)
            artists = get_artists(request, songs)

            return render_to_response(
                    'collection.html',
                    locals(),
                    context_instance=RequestContext(request),
                    )

        elif 'filter_artist' in request.POST:
            artist = request.POST.get('filter_artist')
            terms = ms.search_terms
            songs = filter_songs(request, artist=artist)

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
    else:
        # Do not change anything
        playlists = Playlist.objects.filter(user=request.user)
        return render_to_response(
                'playlists.html',
                locals(),
                context_instance=RequestContext(request),
                )
@login_required
def playlist_remove_item(request, playlist_id, item_id):

    playlist = Playlist.objects.get(id=playlist_id, user=request.user)

    if request.method == "POST":
        item = PlaylistItem.objects.get(id=item_id)
        position = item.position
        item.delete()
        # correct positions of all following items
        for item in playlist.items.all().filter(position__gt=position):
            item.position = item.position-1
            item.save()
        playlist = Playlist.objects.get(id=playlist_id)

    else:
        # Do not change anything
        pass

    return render_to_response(
            'context_playlist.html',
            locals(),
            context_instance=RequestContext(request),
            )

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
def play(request):
    """
    administrate song request. returns urls for audio player <source> tag and song info
    """
    song = None
    if request.method == "POST":
        ms = MusicSession.objects.get(user=request.user)
        song_id = request.POST.get('song_id')
        song = Song.objects.get(id=song_id)

        if "collection" == request.POST.get('source'):
            ms.currently_playing = "collection"
            ms.current_song = song
            ms.save()
        elif "playlist" == request.POST.get('source'):
            playlist = Playlist.objects.get(id=request.POST.get('playlist_id'))
            item = PlaylistItem.objects.get(id=request.POST.get('item_id'))
            playlist.current_position = item.position
            playlist.save()

            ms.currently_playing = "playlist"
            ms.current_playlist = playlist
            ms.save()

    return song_info_response(song)

@login_required
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

        elif "playlist" == ms.currently_playing:
            # attention: multiple songs with same id can be in playlist.items
            pl = ms.current_playlist
            current_position = pl.current_position + 1
            if current_position <= len(pl.items.all()):
                pl.current_position = current_position
                pl.save()
                song = pl.items.get(position=current_position).song

    return song_info_response(song)



#######################      internals     ##################################

@login_required
def rescan(request):
    """
    on POST requests: starts rescan. If rescan in progress, return rescan status.
    on GET requests: return rescan status
    """

    col = Collection.objects.get(user=request.user)

    if col.scan_status == "idle" or col.scan_status == "error":
        if request.method == "POST":
            col.scan_status = "preparing"
            col.save()
            time.sleep(1) # wait for db writeback before starting the rescan. this should avoid deadlocks
            rescan_start.send(sender=None, user=request.user, collection=col)
            return HttpResponse("started")

    elif col.scan_status == "finished":
        col.scan_status = "idle"
        col.save()

    return HttpResponse(col.scan_status)



def song_info_response(song):

    if song == None:
        return HttpResponse("")

    filename = os.path.split(song.path_orig)[-1]
    song_info = {
            'song_id': song.id,
            'title': song.title,
            'artist': song.artist,
            'album': song.album,
            'track': song.track,
            'name': filename,
            'mime': song.mime,
            }
    response = HttpResponse(simplejson.dumps(song_info), mimetype='application/json')
    response['Cache-Control'] = 'no-cache'
    return response

def login(request):
    return HttpResponse("Hi")

def filter_songs(request, terms=None, artist=None):

    dbgprint("search: ", terms)

    if not terms == None:
        if not (type(terms) == unicode or type(terms) == str):
            dbgprint("Invalid type for terms:", type(terms), terms)
            songs = []

        elif len(terms) == 0:
            # return all songs
            songs = Song.objects.filter(user=request.user)

        else:
            term_list = terms.split(" ")
            songs = Song.objects.filter(Q(artist__contains=term_list[0]) | Q(title__contains=term_list[0]) | Q(album__contains=term_list[0]), user=request.user)
            for term in term_list[1:]:
                songs = songs.filter(Q(artist__contains=term) | Q(title__contains=term) | Q(album__contains=term), user=request.user)

    elif not artist == None:
        return Song.objects.filter(artist=artist, user=request.user)

    else:
        songs = []

    return songs

def get_artists(request, songs):

        artists = {}

        if songs == None:
            songs = Song.objects.filter(user=request.user)

        for song in songs:
            if song.artist in artists:
                artists[song.artist] += 1
            else:
                artists[song.artist] = 1

        return artists

