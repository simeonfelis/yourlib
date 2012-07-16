
from django.db import models
from django.contrib.auth.models import User

class Song(models.Model):
    title = models.CharField(max_length=255)
    artist = models.CharField(max_length=255)
    path_orig = models.FilePathField()
    user = models.ForeignKey(User)

    def __unicode__(self):
        return self.artist + " - " + self.title


class Playlist(models.Model):
    name = models.CharField(max_length=255)
    items = models.ManyToManyField(Song, through='PlaylistItem')
    user = models.ForeignKey(User)

    def __unicode__(self):
        return self.name


class PlaylistItem(models.Model):
    song = models.ForeignKey(Song)
    playlist = models.ForeignKey(Playlist)
    position = models.IntegerField()

