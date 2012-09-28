from django.db import models
from django.contrib.auth.models import User

class Song(models.Model):
    class Meta:
        ordering = ['track', 'title', 'path_orig']

    def __unicode__(self):
        return self.title # TODO: include artist name

    title   = models.CharField(max_length=256)
    length  = models.IntegerField()
    track   = models.IntegerField(blank=True, null=True)
    year    = models.IntegerField(blank=True, null=True)
    genre   = models.ForeignKey('Genre', blank=True, null=True)
    album   = models.ForeignKey('Album', blank=True, null=True)
    artist  = models.ForeignKey('Artist', blank=True, null=True)
    mime    = models.CharField(max_length=32)

    path_orig = models.FilePathField(unique=True, max_length=2048)
    time_changed = models.DateTimeField()
    time_added   = models.DateTimeField()
    user = models.ForeignKey(User)

class Genre(models.Model):
    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name

    name = models.CharField(max_length=256, unique=True)

class Artist(models.Model):
    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name

    name = models.CharField(max_length=256, unique=True)

class Album(models.Model):
    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name

    name = models.CharField(max_length=256, unique=True)

class Collection(models.Model):
    user        = models.ForeignKey(User)
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
    status            = models.CharField(max_length=4096)
    search_terms      = models.CharField(max_length=255)
    filter_show       = models.BooleanField(default=False)
    filter_artists    = models.ManyToManyField(Artist, blank=True, null=True)
    filter_albums     = models.ManyToManyField(Album, blank=True, null=True)
    currently_playing = models.CharField(max_length=32)
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

from music import settings as app_settings
import os

if not os.path.isdir(app_settings.FILE_DOWNLOAD_USER_DIR):
    os.makedirs(app_settings.FILE_DOWNLOAD_USER_DIR)

if not os.path.isdir(app_settings.FILE_UPLOAD_TEMP_DIR):
    os.makedirs(app_settings.FILE_UPLOAD_TEMP_DIR)

if not os.path.isdir(app_settings.FILE_UPLOAD_USER_DIR):
    os.makedirs(app_settings.FILE_UPLOAD_USER_DIR)

if not os.path.isdir(app_settings.MUSIC_PATH):
    os.makedirs(app_settings.MUSIC_PATH)


from music.signals import connect_all

connect_all()

