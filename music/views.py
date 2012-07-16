from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.conf import settings

from music.models import Song, Playlist, PlaylistItem
from music.forms import UserLoginForm

import os
from hsaudiotag import auto as tagreader

@login_required
def home(request):

    if request.user.is_authenticated():
        songs = Song.objects.filter(user=request.user)
        playlists = Playlist.objects.filter(user=request.user)
        if 0 == len(playlists):
            print "Creating default playlist for user", request.user
            pl = Playlist(name="default", user=request.user)
            pl.save()
            playlists = Playlist.objects.filter(user=request.user)

    return render_to_response(
            'home.html',
            locals(),
            context_instance=RequestContext(request),
            )

@login_required
def playlist_append(request, song_id):

    if request.method == "POST":
        song = Song.objects.get(id=song_id)
        pl = Playlist.objects.get(name="default", user=request.user)
        item = PlaylistItem(
                playlist = pl,
                song = song,
                position = 1 + len(pl.items.all())
                )
        item.save()
        playlists = Playlist.objects.filter(user=request.user)
        return render_to_response(
                'playlists.html',
                locals(),
                context_instance=RequestContext(request),
                )
    else:
        playlists = Playlist.objects.filter(user=request.user)
        # Do not change anything
        return render_to_response(
                'playlists.html',
                locals(),
                context_instance=RequestContext(request),
                )

@login_required
def play_song(request, song_id):
    print "A song request"

    song = Song.objects.get(id=song_id)
    path = song.path_orig[37:] # strip /home/simeon/workspace/django/yourlib
    response = HttpResponse()
    response["ContentType"] = ""
    response["X-Accel-Redirect"] = path.encode("utf-8")
    print response
    return response

    #return HttpResponse("Would give you file " + path)

@login_required
def rescan(request):
    print "init of library requested."
    print "Clearing database..."
    for song in Song.objects.all():
        song.delete()
    print "Database cleared"

    userdir = os.path.join(settings.MEDIA_ROOT, 'music', request.user.username)

    print "Checking userdir", userdir

    os.path.walk(userdir, add_song, request.user)

    return HttpResponse("Rescan request done")


def login(request):
    return HttpResponse("Hi")

def add_song(user, dirname, files):
    for filename in files:
        path = os.path.join(dirname, filename)

        if not os.path.isfile(path):
            continue

        tags = tagreader.File(path)
        song = Song(
                artist = tags.artist,
                title = tags.title,
                user = user,
                path_orig = path
                )
        song.save()

