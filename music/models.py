import datetime

from django.db import models
from django.contrib.auth.models import User

class Song(models.Model):
    title   = models.CharField(db_index=True, max_length=256)
    length  = models.IntegerField()
    track   = models.IntegerField(blank=True, null=True)
    year    = models.IntegerField(blank=True, null=True)
    genre   = models.ForeignKey('Genre', blank=True, null=True)
    album   = models.ForeignKey('Album', blank=True, null=True)
    artist  = models.ForeignKey('Artist', blank=True, null=True)
    mime    = models.CharField(max_length=32)

    path_orig = models.FilePathField(db_index=True, unique=True, max_length=2048)
    time_changed = models.DateTimeField()
    time_added   = models.DateTimeField()
    user = models.ForeignKey(User)

    created = models.DateTimeField(
                auto_now_add=True,      # TODO: convert deprecated time_added field!
                )

    modified = models.DateTimeField(
                auto_now=True,          # TODO: convert deprecated time_changed field!
                )

    class Meta:
        ordering = ['artist__name', 'album__name', 'track', 'title', 'path_orig']

    def __unicode__(self):
        if self.artist != None:
            return "%s - %s" % (self.artist.name, self.title)
        else:
            return "Unknonw Artist - %s" % (self.title)


class Genre(models.Model):
    name = models.CharField(db_index=True, max_length=256, unique=True)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name


class Artist(models.Model):
    name = models.CharField(db_index=True, max_length=256, unique=True)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name


class Album(models.Model):
    name = models.CharField(db_index=True, max_length=256, unique=True)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name


# TODO: deprecated: model Collection
class Collection(models.Model):
    user        = models.ForeignKey(User)
    scan_status = models.CharField(max_length=32)

class PlaylistItem(models.Model):
    song = models.ForeignKey(Song)
    position = models.IntegerField()

    class Meta:
        ordering = ['position']

    def __unicode__(self):
        return "%d. %s - %s" %(self.position, self.song.artist, self.song.title)


class Playlist(models.Model):
    name            = models.CharField(max_length=256)
    items           = models.ManyToManyField(PlaylistItem)
    user            = models.ForeignKey(User)
    current_position = models.IntegerField()
    created         = models.DateTimeField(
                        auto_now_add=True,
#                        default=datetime.datetime.now()
                        )

    modified        = models.DateTimeField(
                        auto_now=True,
#                        default=datetime.datetime.now(),
                        )

    class Meta:
        ordering = ["name"]

    def __unicode__(self):
        return self.name


class MusicSession(models.Model):
    user = models.ForeignKey(User)
    status            = models.CharField(max_length=4096, blank=True)
    search_terms      = models.CharField(max_length=255, blank=True)
    filter_show       = models.BooleanField(default=False)
    filter_artists    = models.ManyToManyField(Artist, blank=True, null=True)
    filter_albums     = models.ManyToManyField(Album, blank=True, null=True)
    currently_playing = models.CharField(max_length=32)
    current_song      = models.ForeignKey(Song, blank=True, null=True)
    current_playlist  = models.ForeignKey(Playlist, blank=True, null=True)

class Upload(models.Model):
    """
    Administrate upload status
    """
    file        = models.FileField(upload_to="uploads")
    step        = models.CharField(max_length=32)
    step_status = models.IntegerField()
    user        = models.ForeignKey(User)

    created     = models.DateTimeField(
                    auto_now_add=True,
                    )

    modified    = models.DateTimeField(
                    auto_now=True,
                    )

class Download(models.Model):
    step        = models.CharField(max_length=32)
    step_status = models.IntegerField()
    user        = models.ForeignKey(User)
    path        = models.FilePathField()

    created     = models.DateTimeField(
                    auto_now_add=True,
                    )

    modified    = models.DateTimeField(
                    auto_now=True,
                    )


class SharePlaylist(models.Model):
    playlist     = models.ForeignKey("PlayList")
    subscribers  = models.ManyToManyField(User, through="SharePlaylistSubscription")

    def __unicode__(self):
        #return "TODO"
        return "Playlist '%s' from %s to %d users" % (self.playlist.name, self.playlist.user.username, self.subscribers.all().count())

class SharePlaylistSubscription(models.Model):
    created         = models.DateTimeField(
                        auto_now_add=True,                  # set on creation only
#                        default=datetime.datetime.now(),    # convert existing data
                        )
    modified        = models.DateTimeField(
                        auto_now=True,                      # set on modifications only
#                        default=datetime.datetime.now(),    # convert existing data
                        )
    share = models.ForeignKey("SharePlaylist")
    subscriber = models.ForeignKey(User)
    subscriber_accpted = models.BooleanField(default=False)

    def __unicode__(self):
        return "Playlist %s from %s to %s" %(self.share.playlist.name, self.share.playlist.user.username, self.subscriber.username)

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

