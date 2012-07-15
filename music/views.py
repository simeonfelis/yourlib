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
        playlists = Playlist.objects.filter(user=request.user)
        songs = Song.objects.filter(user=request.user)

    return render_to_response(
            'home.html',
            locals(),
            context_instance=RequestContext(request),
            )

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

@login_required
def rescan(request):
    print "init of library requested."
    print "Clearing database..."
    for song in Song.objects.all():
        song.delete()
    print "Database cleared"

    userdir = os.path.join(settings.MEDIA_ROOT, request.user.username, "files")

    print "Checking userdir", userdir

    os.path.walk(userdir, add_song, request.user)

    return HttpResponse("Rescan request done")


def login(request):
    return HttpResponse("Hi")

