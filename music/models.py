
from django.db import models
from django.contrib.auth.models import User

class Song(models.Model):
    def __unicode__(self):
        return self.artist + " - " + self.title

    title = models.CharField(max_length=255)
    artist = models.CharField(max_length=255)
    path_orig = models.FilePathField()
    user = models.ForeignKey(User)

class Playlist(models.Model):
    def __unicode__(self):
        return self.name

    name = models.CharField(max_length=255)
    items =models.ManyToManyField(Song, through='PlaylistItem')
    user = models.ForeignKey(User)

class PlaylistItem(models.Model):
    song = models.ForeignKey(Song)
    playlist = models.ForeignKey(Playlist)
    position = models.IntegerField()
