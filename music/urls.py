from django.conf.urls import patterns, url

urlpatterns = patterns('music.views',
    url(r'^$', 'home_view', name='home'),

    url(r'^play/$', 'play_view'),
    url(r'^play/next$', 'play_next_view'),
    url(r'^play/song/(?P<song_id>\d+)$', 'play_song_view'),

    # this url is deprecating...
    url(r'^sidebar/show/(?P<context>\w+)/.*$', 'sidebar_show_view'),
    url(r'^sidebar/playlists/$', 'sidebar_playlists_view'),

    url(r'^collection/$', 'collection_view'),
    url(r'^collection/songs/$', 'collection_songs_view'),
    url(r'^collection/search/$', 'collection_search_view'),
    #url(r'^collection/more/$', 'collection_more_view'),
    url(r'^collection/browse/$', 'collection_browse_view'),
    url(r'^collection/browse/(?P<column_from>\w+)/$', 'collection_browse_column_view'),
    url(r'^collection/browse/more/(?P<column>\w+)/$', 'collection_browse_more_view'),


    url(r'^playlist/$', 'playlist_view'),
    url(r'^playlist/append/$', 'playlist_append_view'),
    url(r'^playlist/create/$', 'playlist_create_view'),
    url(r'^playlist/delete/$', 'playlist_delete_view'),
    url(r'^playlist/reorder/$', 'playlist_reorder_view'),
    #url(r'^playlist/download/$', 'playlist_download_view'),
    url(r'^playlist/remove/(?P<playlist_id>\d+)/(?P<item_id>\d+)$', 'playlist_remove_item_view'),
    #url(r'^playlist/all/$', 'playlist_all_view'),

    url(r'^rescan$', 'rescan_view'),
    url(r'^upload/file/$', 'upload_file_view'),
    url(r'^upload/show/$', 'upload_show_view'),
    url(r'^upload/status/$', 'upload_file_view'),
    url(r'^upload/clearpending/$', 'upload_clearpending_view'),

    #url(r'^filter/set/(?P<what>\w+)/$', 'filter_set_view'),

    url(r'^accounts/login/.*$', 'login_view', name="login_view"),
    url(r'^accounts/logout/.*$', 'logout_view', name="logout_view"),
)