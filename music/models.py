
from django.db import models
from django.contrib.auth.models import User

PLAYLIST_STATUS_CHOICES = (
        ('stop', 'stop'),
        ('play', 'play'),
)

class Song(models.Model):

    def __unicode__(self):
        return self.artist + " - " + self.title

    title = models.CharField(max_length=256)
    artist = models.CharField(max_length=256)
    path_orig = models.FilePathField()
    user = models.ForeignKey(User)

class PlaylistItem(models.Model):
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
    playing = models.IntegerField()
    status = models.CharField(max_length=32, choices=PLAYLIST_STATUS_CHOICES)

#class MusicUser(models.Model):
#    user = models.ForeignKey(User)
#    playlist = models.ForeignKey(Playlist)

