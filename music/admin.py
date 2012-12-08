from music.models import *
from django.contrib import admin

admin.site.register(Song)
#admin.site.register(PlaylistItem)
admin.site.register(Playlist)
admin.site.register(MusicSession)
admin.site.register(SharePlaylist)
admin.site.register(SharePlaylistSubscription)


admin.site.register(PlaylistItem)