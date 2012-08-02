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
        ordering = ['artist', 'album', 'track', 'title', 'path_orig']

    def __unicode__(self):
        return self.artist + " - " + self.title

    title = models.CharField(max_length=256)
    artist = models.CharField(max_length=256)
    album = models.CharField(max_length=256)
    track = models.IntegerField()
    mime = models.CharField(max_length=32)
    path_orig = models.FilePathField(unique=True, max_length=2048)
    timestamp_orig = models.DateTimeField()
    user = models.ForeignKey(User)
    # in planning:
    # converted = models.ManyToManyField('converted')
    # rename path_orig to path and timestamp_orig to age
    # path should be 'BASE_PATH/User/origs/

# In planning:
# class Converted(models.Model):
#     mime
#     path should be 'BASE_PATH/User/conv/mime/id
#     status 'converting' 'ready'

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

