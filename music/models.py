
from django.db import models
from django.contrib.auth.models import User

CURRENTLY_PLAYING_CHOICES = (
        ('none', 'Playing nothing'),
        ('collection', 'Playing from collection'),
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
    current_position = models.IntegerField()

class MusicSession(models.Model):
    user = models.ForeignKey(User)
    search_terms      = models.CharField(max_length=255, blank=True, null=True)
    currently_playing = models.CharField(max_length=32, choices=CURRENTLY_PLAYING_CHOICES)
    current_song      = models.ForeignKey(Song, blank=True, null=True)
    current_playlist  = models.ForeignKey(Playlist, blank=True, null=True)

