$(document).ready(function () {
    bind_sidebar_playlists();

        function play_song(song_info) {
            $( "#player1_song_info_title" ).html(song_info.title);
            $( "#player1_song_info_artist" ).html(song_info.artist);

            /* rebuild player (maybe firefox issue on invalid sources?) */
            $( "#player1" ).remove();
            $('<audio id="player1" controls="controls" preload="auto"></audio>').appendTo("#player1_temp");

            /* set src url */
            var $song_url='/play/song/' + song_info.song_id;
            if (song_info.mime == "audio/ogg") {
                $('<source id="player1_ogg_source" src="' + $song_url + '" type="audio/ogg"></source>').appendTo("#player1");
            }
            else if (song_info.mime == "audio/mp3") {
                $('<source id="player1_mp3_source" src="' + $song_url + '" type="audio/mp3"></source>').appendTo("#player1");
            }
            $( "#player1" ).bind("ended", on_player1_event_ended);
            $( "#player1" )[0].pause();
            $( "#player1" )[0].load();
            $( "#player1" )[0].play();
        };

        function on_player1_event_ended() {
            $.post("/play/next", {"csrfmiddlewaretoken": csrf_token}, function(song_info) {
                if (song_info=="") {
                    return;
                }
                else {
                    play_song(song_info);
                }
            });
        };

        function bind_playlist() {
            $( ".btn_playlist_play" ).click(function() {
                return false; // Don't do anything else
            });

            $( ".btn_playlist_item_play" ).click(function() {
                var $data = {
                    'csrfmiddlewaretoken': csrf_token,
                    'song_id'            : $(this).attr("data-song_id"),
                    'playlist_id'        : $(this).attr("data-playlist_id"),
                    'item_id'            : $(this).attr("data-item_id"),
                    'source'             : 'playlist',
                };
                $.post("/play/", $data, function(song_info) {
                    play_song(song_info);
                });
                return false; // Don't do anything else
            });

            $( ".btn_playlist_item_remove" ).click(function() {
                var playlist_id = $(this).attr("data-playlist_id");
                var item_id = $(this).attr("data-item_id");

                var sel = "#playlist_content_" + playlist_id;
                var url = "/playlist/remove/" + playlist_id + "/" + item_id;
                var $data = {
                    'csrfmiddlewaretoken': csrf_token,
                };
                $( sel ).load(url, $data, function() {
                    bind_playlist();
                });
                return false; // Don't do anything else
            });
        }

        function bind_sidebar_playlists() {
            $( ".btn_context_playlist" ).click(function() {
                var $data = {
                    'csrfmiddlewaretoken': csrf_token,
                    'playlist_id': $(this).attr("data-playlist_id"),
                };
                $( "#context_content" ).load("/context/playlist/",  $data, function() {
                    bind_playlist();
                    // alert("context playlist loaded");
                });
            });

        }

        function bind_collection_songs() {
            $( ".btn_collection_play_song" ).click(function() {
                var $data = {
                    'csrfmiddlewaretoken': csrf_token,
                    'song_id': $(this).attr("data-song_id"),
                    'source' : 'collection',
                };
                $.post("/play/", $data, function(song_info) {
                    play_song(song_info);
                });
                return false;
            });
            $( ".btn_collection_append_to_playlist" ).click(function() {
                /* $(this) is expected to be a collection song item */
                var $playlist_id = $(this).attr("data-playlist_id");
                var $song_id = $(this).attr("data-song_id");
                var $data = {'playlist_id' : $playlist_id, 'song_id': $song_id, "csrfmiddlewaretoken": csrf_token};
                $( "#playlists" ).load("/playlist/append/", $data, function() {
                    // TODO: increase only number of playlist items in sidebar
                    bind_sidebar_playlists();
                });
                //var sel = "#playlist_" + $playlist_id;
                //$( sel ).load("/playlist/append/", $data, function() {
                //    //alert("New playlist set");
                //});
                return false; // don't do anything else
            });
        };

        function bind_collection_search() {
            $( "#context_collection_search" ).change(function() {
                $( "#context_collection_search_status" ).html("Started");
                var $terms = $(this).val();
                var $data = {"csrfmiddlewaretoken": csrf_token, "terms": $terms};
                $( "#context_collection_songs").load("/search/", $data, function() {
                    $( "#context_collection_search_status" ).html("Finished");
                    bind_collection_songs();
                    // now bind handlers for search result...
                });
            });
        };

        $( "#btn_rescan_library" ).click(function() {
            $( "#rescan_status" ).html("Rescan requested. This might take a while....");
            var data = {"csrfmiddlewaretoken": csrf_token, "playlist_name": $(this).val()};
            $.post("/rescan", data, function() {
            })
            .success(function() { $( "#rescan_status" ).html("Rescan done"); })
            .error(function() { $( "#rescan_status" ).html("Error during rescan"); });
            return false; // don't do anything else
        });

        $( "#btn_context_collection" ).click(function() {
            var $data = {"csrfmiddlewaretoken": csrf_token};
            $( "#context_content" ).load("/context/collection/", $data, function() {
                bind_collection_search();
            });
        });

        $( "#create_new_playlist" ).change(function() {
            var data = {"csrfmiddlewaretoken": csrf_token, "playlist_name": $(this).val()};
            $.post("/playlist/create/", data, function(new_playlist) {
                $( "#playlists" ).add(new_playlist);
            });
        });
// deprecated
//        $( "#search_input" ).change(function() {
//            $( "#search_result_container" ).html("Started");
//            var $terms = $(this).val();
//            var jqxhr = $.post("/search/" + $terms, {"csrfmiddlewaretoken": csrf_token}, function(results) {
//                $( "#search_result_container" ).html(results);
//                // bind play.click handler
//                $( ".btn_play_search_result" ).click(function() {
//                    var $result_id = parseInt($(this).attr("data-search_result_id"));
//                    $.post("/play/result/" + $result_id, {"csrfmiddlewaretoken": csrf_token}, function(song_info) {
//                        play_song(song_info);
//                    })
//                    return false; // don't do anything anymore
//                });
//                // bind append_to_playlist handler
//                $( ".btn_append_to_playlist" ).click(function() {
//                    /* $(this) is expected to be a playlist song item (not a playlist song item) */
//                    var $playlist_id = $(this).attr("data-playlist_id");
//                    var $song_id = $(this).attr("data-song_id");
//                    var $data = {'playlist_id' : $playlist_id, 'song_id': $song_id, "csrfmiddlewaretoken": csrf_token};
//                    var sel = "#playlist_" + $playlist_id;
//                    $( sel ).load("/playlist/append/", $data, function() {
//                        //alert("New playlist set");
//                    });
//                    return false; // don't do anything else
//                });
//            })
//            .success(function() {/*alert("Second success");*/})
//            .error(function() {/*alert("error");*/})
//            .complete(function() {/*alert("complete");*/});
//            jqxhr.complete(function() {/*alert("second complete");*/});
//        });

        $( "#btn_player1_next" ).click(function() {
            on_player1_event_ended();
        });
        $( ".btn_playlist_item_remove" ).click(function() {
            var $playlist_id = $(this).attr("data-playlist_id");
            var $item_id = $(this).attr("data-item_id");
            $.post("/playlist/remove/item/" + $playlist_id + "/" + $item_id, {"csrfmiddlewaretoken": csrf_token}, function(new_playlist) {
                $( "#playlist_1" ).remove();
                $( "#playlists" ).append(new_playlist);
            });
        });
        $( ".btn_play_song" ).click(function() {
            var $song_id = parseInt(this.id.substring(14));
            var $artist = $(this).attr("data-artist");
            var $title = $(this).attr("data-title");
            var $mime = $(this).attr("data-mime");

            var $song_info = {
                'song_id' : $song_id,
                'artist': $artist,
                'title': $title,
                'mime': $mime,
            };
            play_song($song_info);
            return false; // don't do anything anymore
        });
});

