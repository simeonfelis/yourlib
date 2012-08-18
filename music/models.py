from django.db import models
from django.contrib.auth.models import User

CURRENTLY_PLAYING_CHOICES = (
        ('none', 'Playing nothing'),
        ('collection', 'Playing from collection'),
        ('playlist', 'Playing from playlist'),
)

UPLOAD_FILE_STEPS = [
        "idle",
        "uploading",
        "copying",     # move to user's upload dir
        "decompress",  # if zip, deflate to global tmp, delete deflates afterwards
        "structuring", # if supported file(s), read tags, determine target
                       # locations and put files file(s) there
        "error",
        ]


class Song(models.Model):
    class Meta:
        ordering = ['track', 'title', 'path_orig']

    def __unicode__(self):
        return self.title # TODO: include artist name

    title = models.CharField(max_length=256)
    track = models.IntegerField()

    genre = models.CharField(max_length=256)
    mime = models.CharField(max_length=32)

    path_orig = models.FilePathField(unique=True, max_length=2048)
    timestamp_orig = models.DateTimeField()
    user = models.ForeignKey(User)

class Artist(models.Model):
    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name

    name = models.CharField(max_length=256, unique=True)
    songs = models.ManyToManyField(Song)

class Album(models.Model):
    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name

    name = models.CharField(max_length=256)
    songs = models.ManyToManyField(Song)

class Collection(models.Model):
    user = models.ForeignKey(User)
    scan_status = models.CharField(max_length=32)

class PlaylistItem(models.Model):
    class Meta:
        ordering = ['position']
    def __unicode__(self):
        return str(self.position) + ". " + self.song.artist + " - " + self.song.title

    song = models.ForeignKey(Song)
    position = models.IntegerField()

class Playlist(models.Model):

    def __unicode__(self):
        return self.name

    name = models.CharField(max_length=256)
    items = models.ManyToManyField(PlaylistItem)
    user = models.ForeignKey(User)
    current_position = models.IntegerField()

class MusicSession(models.Model):
    user = models.ForeignKey(User)
    search_terms      = models.CharField(max_length=255)
    filter_show       = models.BooleanField(default=False)
    filter_artists    = models.ManyToManyField(Artist, blank=True, null=True)
    filter_albums     = models.ManyToManyField(Album, blank=True, null=True)
    currently_playing = models.CharField(max_length=32, choices=CURRENTLY_PLAYING_CHOICES)
    current_song      = models.ForeignKey(Song, blank=True, null=True)
    current_playlist  = models.ForeignKey(Playlist, blank=True, null=True)

class Upload(models.Model):
    """
    only available during upload processes, deleted afterwards
    """
    file        = models.FileField(upload_to="uploads")
    step        = models.CharField(max_length=32)
    step_status = models.IntegerField()
    user        = models.ForeignKey(User)

class Download(models.Model):
    step        = models.CharField(max_length=32)
    step_status = models.IntegerField()
    user        = models.ForeignKey(User)
    path        = models.FilePathField()

from django.conf import settings
import os

if not os.path.isdir(settings.MUSIC_PATH):
    os.makedirs(settings.MUSIC_PATH)

if not os.path.isdir(settings.FILE_UPLOAD_TEMP_DIR):
    os.makedirs(settings.FILE_UPLOAD_TEMP_DIR)

if not os.path.isdir(settings.FILE_UPLOAD_USER_DIR):
    os.makedirs(settings.FILE_UPLOAD_USER_DIR)

from music.signals import connect_all

connect_all()

