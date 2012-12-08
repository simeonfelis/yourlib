from django.conf.urls import patterns, url

urlpatterns = patterns('music.views',
    url(r'^username_validation/$', 'username_validation_view'),

    url(r'^$', 'home_view', name='home'),

#    url(r'^play/$', 'home_view', name="song_base_url"),  # for javascript in template to have a flexible url
    url(r'^play/(?P<play_id>\d+)/$', 'play_view', name="play"),

#    url(r'^play/$', 'play_view'),
#    url(r'^play/next$', 'play_next_view'),
#    url(r'^play/song/(?P<song_id>\d+)$', 'play_song_view'),
#
#    # TODO: these urls are deprecating...
#    url(r'^sidebar/show/(?P<context>\w+)/.*$', 'sidebar_show_view'),
#    url(r'^sidebar/playlists/$', 'sidebar_playlists_view'),
#
    url(r'^collection/$',                                'collection_view', name="collection"),
    url(r'^collection/play/$',                           'collection_play_view', name="collection_play"),
    url(r'^collection/search/$',                         'collection_search_view', name="collection_search"),
#    (r'^collection/more/$', 'collection_more_view'),
#    url(r'^collection/settings/$', 'collection_settings_view', name="collection_settings"),
#
    url(r'^collection/browse/$',                         'collection_browse_view', name="collection_browse"),
    url(r'^collection/browse/play/$',                    'collection_play_view', name="collection_browse_play"),
    url(r'^collection/browse/(?P<column>\w+)/$',         'collection_browse_column_view'),
    url(r'^collection/browse/(?P<column>\w+)/more/$',    'collection_browse_column_more_view'),
    url(r'^settings/collection/browse/$',                'settings_collection_browse_view', name="settings_collection_browse"),
#    url(r'^collection/browse/more/(?P<column>\w+)/$', 'collection_browse_more_view'),
#
#    url(r'^playlists/$',                                 'playlists_view', name="playlists"), # playlists overview
    url(r'^playlist/create/$',                           'playlist_create_view', name="playlist_create"),
    url(r'^playlist/(?P<playlist_id>\d+)/$',             'playlist_view', name="playlist"), # show a single playlist
    url(r'^playlist/(?P<playlist_id>\d+)/delete/$',      'playlist_delete_view'),
    url(r'^playlist/(?P<playlist_id>\d+)/play/$',        'playlist_play_view'),
    url(r'^playlist/(?P<playlist_id>\d+)/reorder/$',     'playlist_reorder_view'),
    url(r'^playlist/(?P<playlist_id>\d+)/append/$',      'playlist_append_view'),
    url(r'^playlist/(?P<playlist_id>\d+)/remove_item/$', 'playlist_remove_item_view'),
    url(r'^playlist/(?P<playlist_id>\d+)/share/$',       'playlist_share_view'),
    url(r'^playlist/(?P<playlist_id>\d+)/unshare/$',     'playlist_unshare_view'),
#    url(r'^playlist/$', 'playlist_view', name="playlist"), # playlist overview
#    url(r'^playlist/create/$', 'playlist_create_view'),
#    url(r'^playlist/delete/$', 'playlist_delete_view'),
#    url(r'^playlist/reorder/$', 'playlist_reorder_view'),
#    #url(r'^playlist/download/$', 'playlist_download_view'),
#    url(r'^playlist/remove/(?P<playlist_id>\d+)/(?P<item_id>\d+)$', 'playlist_remove_item_view'),
#    #url(r'^playlist/all/$', 'playlist_all_view'),

    url(r'^shares/$', 'shares_view', name="shares"),
    url(r'^shares/playlist/(?P<playlist_id>\d+)/$', 'shares_playlist_view', name="shares_playlist"),
    url(r'^shares/playlist/(?P<playlist_id>\d+)/play/$', 'playlist_play_view'),


#    url(r'^rescan$', 'rescan_view'),
    url(r'^upload/$', "upload_view", name="upload"),
#    url(r'^upload/file/$', 'upload_file_view'),
#    url(r'^upload/show/$', 'upload_show_view'),
#    url(r'^upload/status/$', 'upload_file_view'),
#    url(r'^upload/clearpending/$', 'upload_clearpending_view'),
#
#    #url(r'^filter/set/(?P<what>\w+)/$', 'filter_set_view'),
#
    url(r'^accounts/login/.*$', 'login_view', name="login_view"),
    url(r'^accounts/logout/.*$', 'logout_view', name="logout_view"),
)