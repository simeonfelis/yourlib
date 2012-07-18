
from django.db import models
from django.contrib.auth.models import User

PLAYLIST_STATUS_CHOICES = (
        ('stop', 'stop'),
        ('play', 'play'),
)

CURRENTLY_PLAYING_CHOICES = (
        ('none', 'Playing nothing'),
        ('search', 'Playing from search results'),
        ('playlist', 'Playing from playlist'),
)


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

class SearchResult(models.Model):
    song = models.ForeignKey(Song)

class Search(models.Model):
    user = models.ForeignKey(User)
    results = models.ManyToManyField(SearchResult, blank=True, null=True)
    playing = models.ForeignKey(SearchResult, blank=True, null=True, related_name='+')

class MusicSession(models.Model):
    user = models.ForeignKey(User)
    currently_playing = models.CharField(max_length=32, choices=CURRENTLY_PLAYING_CHOICES)
    search = models.ForeignKey(Search, blank=True, null=True)
    playlist = models.ForeignKey(Playlist, blank=True, null=True)

