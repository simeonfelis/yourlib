from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.utils import simplejson
from django.utils.timezone import utc
from django.conf import settings
from django.db.models import Q

from music.models import Song, Playlist, PlaylistItem, MusicSession
#from music.forms import UserLoginForm

import os, datetime
import mutagen as tagreader

@login_required
def home(request):

    if request.user.is_authenticated():
        playlists = Playlist.objects.filter(user=request.user)
        if 0 == len(playlists):
            print "Creating default playlist for user", request.user
            pl = Playlist(name="default", user=request.user, current_position=0)
            pl.save()
            playlists = Playlist.objects.filter(user=request.user)

        # current status
        try:
            music_session = MusicSession.objects.get(user=request.user)
        except MusicSession.DoesNotExist:
            print "Creating music session for user", request.user
            music_session = MusicSession(user=request.user, currently_playing='none', search_terms='')
            music_session.save()

        songs = filter_songs(request, terms=music_session.search_terms)
        if len(songs) > 200:
            print "To many songs"
        # not stable
        #if len(music_session.search_terms) > 0:
        #    artists = get_artists(request, songs)
        #else:
        #    # all artists
        #    artists = get_artists(request, None)

    print music_session.currently_playing
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
            print "context playlist", request.POST
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
    print "New song play request"
    if request.method == "POST":
        ms = MusicSession.objects.get(user=request.user)
        song_id = request.POST.get('song_id')
        song = Song.objects.get(id=song_id)

        if "collection" == request.POST.get('source'):
            print "Currently song source: collection"
            ms.currently_playing = "collection"
            ms.current_song = song
            ms.save()
        elif "playlist" == request.POST.get('source'):
            print "Currently song source: playlist"
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
    if request.method == "POST":
        print "rescan of library requested."
        print "check for orphans"
        for s in Song.objects.filter(user=request.user):
            if not os.path.isfile(s.path_orig):
                print "Deleting orphan file", s.path_orig
                s.delete()

        userdir = os.path.join(settings.MUSIC_PATH, request.user.username)
        print "scan music folder", userdir
        for root, dirs, files in os.walk(userdir):
            add_song(root, files, request.user)

        return HttpResponse("Rescan request done")

    return HttpResponse("Use POST request! and fuck you, chrome prefetch!")

def add_song(dirname, files, user):
    for filename in files:
        path = os.path.join(dirname, filename)

        if not os.path.isfile(path):
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
                continue
            else:
                # reread tags and store it to song. Therefore, leave variable song != None
                pass

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
            print "Adding file", path
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
            print "Updating file", path
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
            print "Database error on file", path, e

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

    if not terms == None:
        if not type(terms) == unicode:
            print "Invalid type for terms: ", type(terms), terms
            raise Exception("Invalid type for terms: " + str(type(terms)) + " content: " + str(terms))

        if len(terms) == 0:
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


