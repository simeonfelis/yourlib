from django.db import models

class Song(models.Model):
    def __unicode__(self):
        return self.artist + " - " + self.title

    title = models.CharField(max_length=255)
    artist = models.CharField(max_length=255)
    path_orig = models.FilePathField()

class Playlist(models.Model):
    def __unicode__(self):
        return self.name

    name = models.CharField(mox_length=255)
    items =models.ManyToManyField(Song, through='PlaylistItem')

class PlaylistItem(models.Model):
    song = models.ForeignKey(Song)
    playlist = models.ForeignKey(Playlist)
    position = models.IntegerField()
