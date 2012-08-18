from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'music.views.home', name='home'),
    url(r'^play/$', 'music.views.play'),
    url(r'^play/song/(?P<song_id>\d+)$', 'music.views.play_song'),
    url(r'^play/next$', 'music.views.play_next'),
    url(r'^search/$', 'music.views.search'),
    url(r'^filter/(?P<what>\w+)/$', 'music.views.filter'),
    #url(r'^play/result/(?P<result_id>\d+)$', 'music.views.play_result'),
    #url(r'^play/playlist/(?P<playlist_id>\d+)$', 'music.views.play_playlist'),
    url(r'^playlist/append/$', 'music.views.playlist_append'),
    url(r'^playlist/create/$', 'music.views.playlist_create'),
    url(r'^playlist/delete/$', 'music.views.playlist_delete'),
    url(r'^playlist/reorder/$', 'music.views.playlist_reorder'),
    url(r'^playlist/download/$', 'music.views.playlist_download'),
    url(r'^playlist/remove/(?P<playlist_id>\d+)/(?P<item_id>\d+)$', 'music.views.playlist_remove_item'),
    url(r'^playlist/all/$', 'music.views.playlists'),
    url(r'^rescan$', 'music.views.rescan'),
    url(r'^context/(?P<selection>\w+)/.*$', 'music.views.context'),
    url(r'^upload/$', 'music.views.upload'),

    url(r'^accounts/login/.*$', 'django.contrib.auth.views.login'),
    url(r'^accounts/logout/.*$', 'django.contrib.auth.views.logout'),
    # url(r'^music/', include('music.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
