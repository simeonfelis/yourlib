from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.utils import simplejson
from django.conf import settings
from django.db.models import Q

from music.models import Song, Playlist, PlaylistItem, MusicSession
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
            pl = Playlist(name="default", user=request.user, current_position=0)
            pl.save()
            playlists = Playlist.objects.filter(user=request.user)

        music_session = MusicSession.objects.filter(user=request.user)
        if 0 == len(music_session):
            print "Creating music session for user", request.user
            ms = MusicSession(user=request.user, currently_playing='none')
            ms.save()
            music_session = MusicSession.objects.filter(user=request.user)
        music_session = music_session[0]
        print "music_session", music_session.currently_playing
        # put last saved status here!

    return render_to_response(
            'home.html',
            locals(),
            context_instance=RequestContext(request),
            )

@login_required
def context(request, selection):
    if request.method == "POST":
        ms = MusicSession.objects.get(user=request.user)
        if selection == "collection":
            ms.context = "collection"
            ms.save()
            return render_to_response(
                    "context_collection.html",
                    locals(),
                    context_instance=RequestContext(request),
                    )

        elif selection == "playlist":
            print "context playlist", request.POST
            playlist_id = request.POST.get('playlist_id')
            playlist = Playlist.objects.get(id=playlist_id)
            return render_to_response(
                    "context_playlist.html",
                    locals(),
                    context_instance=RequestContext(request),
                    )

    return HttpResponse("")

#TODO: increase performance
@login_required
def search(request, terms):

    if request.method == "POST":
        if 'terms' in request.POST:
            terms = request.POST.get('terms')
        elif "" == terms:
            return HttpResponse("")

        ms = MusicSession.objects.get(user=request.user)
        ms.search_terms = terms
        ms.save()

        songs = filter_songs(request, terms)

        print "Found", len(songs), "songs for terms", terms

        playlists = Playlist.objects.filter(user=request.user)

        return render_to_response(
                'collection.html',
                locals(),
                context_instance=RequestContext(request),
                )

    # return nothing on GET requests
    return HttpResponse("")

@login_required
def playlist_create(request):
    if request.method == "POST":
        name = request.POST.get('playlist_name')
        playlist = Playlist(name=name, user=request.user, playing=0, status="stop")
        playlist.save()
        return render_to_response(
                "playlist.html",
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
    response = HttpResponse()
    response["Content-Type"] = ""
    response["X-Accel-Redirect"] = path.encode("utf-8")
    print response
    return response

@login_required
def play(request):
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
            songs = filter_songs(request, ms.search_terms)
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

#@login_required
#def play_playlist(request, playlist_id):
#    if request.method == "POST":
#        pl = Playlist.objects.get(id=playlist_id)
#        pl.status = "play"
#        playing = 1
#        pl.playing = playing
#        pl.save()
#
#        ms = MusicSession.objects.get(user=request.user)
#        ms.currently_playing = "playlist"
#        ms.playlist = pl
#        ms.save()
#        item = PlaylistItem.objects.filter(playlist__id=playlist_id, position=playing)[0]
#        return song_info_response(item.song)

#@login_required
#def play_result(request, result_id):
#    if request.method == "POST":
#        result=SearchResult.objects.get(id=result_id)
#
#        search = Search.objects.get(user=request.user)
#        search.playing = result
#        search.save()
#        ms = MusicSession.objects.get(user=request.user)
#        ms.currently_playing = "search"
#        ms.save()
#        return song_info_response(result.song)
#
#    return HttpResponse("")

# TODO: perfomance!
@login_required
def rescan(request):
    print "init of library requested."
    print "Clearing database..."
    for s in Song.objects.all():
        print "deleting song", s
        s.delete()
    print "Database cleared"

    userdir = os.path.join(settings.MUSIC_PATH)

    print "Checking userdir", userdir

    os.path.walk(userdir, add_song, request.user)

    return HttpResponse("Rescan request done")

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
            artist    = tags['artist'][0].encode('utf-8')
        except:
            artist = "Unknown"
        try:
            title     = tags['title'][0].encode('utf-8')
        except:
            title = "Unknown"
        try:
            track     = int(tags['tracknumber'][0].encode('utf-8').split('/')[0])
        except:
            track = 0
        try:
            album     = tags['album'][0].encode('utf-8')
        except:
            album = "Unknown"

        song = Song(
                artist    = artist,
                title     = title,
                album     = album,
                track     = track,
                mime      = mime,
                user      = user,
                path_orig = path
                )
        try:
            song.save()
        except Exception, e:
            print "Database error on file", path, e
            print "Probably wrong encoded file name or wrong filesystem character set chosen. or the database is locked."

def filter_songs(request, terms):
    term_list = terms.split(" ")
    songs = Song.objects.filter(Q(artist__contains=term_list[0]) | Q(title__contains=term_list[0]) | Q(album__contains=term_list[0]), user=request.user)
    for term in term_list[1:]:
        songs = songs.filter(Q(artist__contains=term) | Q(title__contains=term) | Q(album__contains=term), user=request.user)

    return songs

