from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.utils import simplejson
from django.utils.encoding import iri_to_uri
from django.conf import settings
from django.db.models import Q

from music.models import Song, Playlist, PlaylistItem, Search, SearchResult, MusicSession
#from music.forms import UserLoginForm

import os
import mutagen as tagreader

@login_required
def home(request):

    if request.user.is_authenticated():
        songs = Song.objects.filter(user=request.user)
        playlists = Playlist.objects.filter(user=request.user)
        if 0 == len(playlists):
            print "Creating default playlist for user", request.user
            pl = Playlist(name="default", user=request.user, playing=0, status="stop")
            pl.save()
            playlists = Playlist.objects.filter(user=request.user)

        music_session = MusicSession.objects.filter(user=request.user)
        if 0 == len(music_session):
            print "Creating music session for user", request.user
            ms = MusicSession(user=request.user, currently_playing='none')
            ms.save()
            music_session = MusicSession.objects.filter(user=request.user)

    return render_to_response(
            'home.html',
            locals(),
            context_instance=RequestContext(request),
            )

@login_required
def play_playlist(request, playlist_id):
    if request.method == "POST":
        pl = Playlist.objects.get(id=playlist_id)
        pl.status = "play"
        playing = 1
        pl.playing = playing
        pl.save()
        item = PlaylistItem.objects.filter(playlist__id=playlist_id, position=playing)[0]
        return song_info_response(item.song)

@login_required
def play_next(request):
    if request.method == "POST":
        currently_playing = MusicSession.objects.get(user=request.user).currently_playing

        if "none" == currently_playing:
            song = None

        elif "search" == currently_playing:
            search = Search.objects.get(user=request.user)
            current = search.playing
            found = False
            song = None
            for result in search.results.all():
                #print "play from search: comparing", current.id, current.song, "with", result.id, result.song
                if found:
                    song = result.song
                    #print "match, returning", result.id, result.song
                    break
                elif result.id == current.id:
                    found = True

            if not None == song:
                search.playing = result
                search.save()

        elif "playlist" == currently_playing:
            pl = Playlist.objects.get(id=1)
            playing = pl.playing + 1
            pl.playing = playing
            item = PlaylistItem.objects.filter(playlist__id=1, position=playing)[0]
            song = item.song
        else:
            song = None

        if not song == None:
            return song_info_response(song)

    return HttpResponse("")

#TODO: increase performance
@login_required
def search(request, terms):
    print "Terms:", terms
    if "" == terms:
        return HttpResponse("")

    if request.method == "POST":
        term_list = terms.split(" ")
        songs = Song.objects.filter(Q(artist__contains=term_list[0]) | Q(title__contains=term_list[0]), user=request.user)
        for term in term_list[1:]:
            songs = songs.filter(Q(artist__contains=term) | Q(title__contains=term), user=request.user)

        print "Found", len(songs), "songs for terms", terms

        # Save search results to db
        search = Search.objects.filter(user=request.user)
        if 0 == len(search):
            # if user has no search db entry, create new one
            search = Search(user=request.user)
        else:
            # clear old search results
            search = search[0]
            search.results.clear() # performance!
        search.save()

        for song in songs: # performance
            result = SearchResult(song=song)
            result.save()
            search.results.add(result)

        search.save()

        return render_to_response(
                'search_results.html',
                locals(),
                context_instance=RequestContext(request),
                )

    # return nothing on GET requests
    return HttpResponse("")


@login_required
def playlist_append(request, song_id):

    if request.method == "POST":
        song = Song.objects.get(id=song_id)
        pl = Playlist.objects.get(name="default", user=request.user)
        item = PlaylistItem(
#                playlist = pl,
                song = song,
                position = 1 + len(pl.items.all())
                )
        item.save()
        playlist = Playlist.objects.get(id=1)
        playlist.items.add(item)
        playlist.save()
        return render_to_response(
                'playlist.html',
                locals(),
                context_instance=RequestContext(request),
                )
    else:
        # Do not change anything
        playlist = Playlist.objects.get(id=1)
        return render_to_response(
                'playlist.html',
                locals(),
                context_instance=RequestContext(request),
                )
@login_required
def playlist_remove_item(request, playlist_id, item_id):
    print playlist_id, item_id

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
            'playlist.html',
            locals(),
            context_instance=RequestContext(request),
            )

@login_required
def play_song(request, song_id):
    song = Song.objects.get(id=song_id)
    path = "/music" + song.path_orig[len(settings.MUSIC_PATH):] # append "/music", strip prefix (/media....)
    #path = iri_to_uri(path)
    response = HttpResponse()
    response["Content-Type"] = ""
    response["X-Accel-Redirect"] = path.encode("utf-8")
    print response
    return response

@login_required
def play_result(request, result_id):
    if request.method == "POST":
        result=SearchResult.objects.get(id=result_id)

        search = Search.objects.get(user=request.user)
        search.playing = result
        search.save()
        ms = MusicSession.objects.get(user=request.user)
        ms.currently_playing = "search"
        ms.save()
        return song_info_response(result.song)

    return HttpResponse("")

@login_required
def rescan(request):
    print "init of library requested."
    print "Clearing database..."
    for song in Song.objects.all():
        song.delete()
    print "Database cleared"

    userdir = os.path.join(settings.MUSIC_PATH)

    print "Checking userdir", userdir

    os.path.walk(userdir, add_song, request.user)

    return HttpResponse("Rescan request done")

def song_info_response(song):
    song_info = {
            'song_id': song.id,
            'title': song.title,
            'artist': song.artist,
            'mime': song.mime,
            }
    response = HttpResponse(simplejson.dumps(song_info), mimetype='application/json')
    response['Cache-Control'] = 'no-cache'
    return response

def login(request):
    return HttpResponse("Hi")

def add_song(user, dirname, files):
    for filename in files:
        path = os.path.join(dirname, filename)

        if not os.path.isfile(path):
            continue

        try:
            tags = tagreader.File(path, easy=True)
        except Exception, e:
            print "Error reading tags on file", path, e
            continue

        # ignore everything except ogg and mp3
        if type(tags) == tagreader.oggvorbis.OggVorbis:
            mime = "audio/ogg"
        elif type(tags) == tagreader.mp3.EasyMP3:
            mime = "audio/mp3"
        elif type(tags) == type(None):
            # don't even warn
            continue
        else:
            print "Ignoring file", path, "because of mime (", type(tags), ")"
            continue

        try:
            song = Song(
                    artist    = tags['artist'][0].encode('utf-8'),
                    title     = tags['title'][0].encode('utf-8'),
                    mime      = mime,
                    user      = user,
                    path_orig = path
                    )
        except Exception, e:
            print "Error reading tags on file", path, e
        else:
            try:
                song.save()
            except Exception, e:
                print "Database error on file", path, e
                print "Probably wrong encoded file name or wrong filesystem character set chosen."

