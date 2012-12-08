from music.models import Song, MusicSession, SharePlaylist, SharePlaylistSubscription, PlaylistItem, Playlist, Upload, Download, Genre, Artist
from django.contrib import admin


class SongAdmin(admin.ModelAdmin):
    list_display = ("artist", "album", "title", "track", "year", "length", "user", "time_added", "time_changed",)
    list_filter = ["user", "artist", "genre"]
    search_fields = ["artist__name", "album__name", "title"]

admin.site.register(Song, SongAdmin)


class PlaylistAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "items_count", "current_position", "created", "modified", )
    list_filter = ["user", ]
    search_fields = ["name"]

admin.site.register(Playlist, PlaylistAdmin)

class SharePlaylistAdmin(admin.ModelAdmin):
    list_display = ("playlist", "subscribers_count")
    list_filter = ["playlist__user"]
    search_fields = ["playlist__name"]

admin.site.register(SharePlaylist, SharePlaylistAdmin)

class SharePlaylistSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("get_playlist_name", "get_owner_name", "subscriber", "subscriber_accpted", "created", "modified")
    list_filter = ["share__playlist__user", "subscriber", "subscriber_accpted"]
    search_fields = ["playlist__name"]

    def get_playlist_name(self, obj):
        return obj.share.playlist.name
    get_playlist_name.short_description = "Playlist"

    def get_owner_name(self, obj):
        return obj.share.playlist.user.username
    get_owner_name.short_description = "Owner"

admin.site.register(SharePlaylistSubscription, SharePlaylistSubscriptionAdmin)

class MusicSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "currently_playing", "current_song", "current_playlist", "get_last_login")
    search_fields = ["user__username", "current_song__title", "current_song__artist__name"]

    def get_last_login(self, obj):
        return obj.user.last_login
    get_last_login.short_description = "Last login"

admin.site.register(MusicSession, MusicSessionAdmin)

class PlaylistItemAdmin(admin.ModelAdmin):
    list_display = ("song", "position", "playlist", "get_playlist_user")
    list_filter = ["playlist__user"]
    search_fields = ["playlist__name", "song__title", "song__artist__name"]

    def get_playlist_user(self, obj):
        return obj.playlist.user.username
    get_playlist_user.short_description = "User"

admin.site.register(PlaylistItem, PlaylistItemAdmin)

class ArtistAdmin(admin.ModelAdmin):
    list_display = ("name", "get_songs_count")
    search_fields = ["name"]

    def get_songs_count(self, obj):
        return obj.song_set.all().count()
    get_songs_count.short_description = "Songs"

admin.site.register(Artist, ArtistAdmin)

class GenreAdmin(admin.ModelAdmin):
    list_display = ("name", "get_songs_count")
    search_fields = ["name"]

    def get_songs_count(self, obj):
        return obj.song_set.all().count()
    get_songs_count.short_description = "Songs"

admin.site.register(Genre, GenreAdmin)

class UploadAdmin(admin.ModelAdmin):
    list_display = ("step", "step_status", "user", "created", "modified")
    list_filters = ["user", "step_status"]

admin.site.register(Upload, UploadAdmin)

class DownloadAdmin(admin.ModelAdmin):
    list_display = ("step", "step_status", "user", "created", "modified")
    list_filters = ["user", "step_status"]

admin.site.register(Download, DownloadAdmin)

