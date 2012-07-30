function Collection() {
    this.bind = function(){} // stub

    this.song_play = function() {
        var $data = {
            'csrfmiddlewaretoken': csrf_token,
            'song_id': $(this).attr("data-song_id"),
            'source' : 'collection',
        };
        $.post("play/", $data, function(song_info) {
            player1.play_song(song_info);
        });
        return false;
    }

    this.search = function() {
        $( "#context_collection_search_status" ).html("Started");
        var $data = {
            "csrfmiddlewaretoken": csrf_token,
            "terms": $( "#collection_search_terms" ).val(),
        };
        $( "#context_collection_container").load("search/", $data, function(response, status, xhr) {
            if (status == "error") {
                $( "#context_collection_search_status" ).html("Error " + xhr.status + " " + xhr.statusText);
            }
            else {
                $( "#context_collection_search_status" ).html("Finished");
            }
        });
        return false; // Don't do anything else
    }

    this.get_more_results = function() {
            var so_far = $( ".song_item" ).length;
            var $data = {
                /* 'csrfmiddlewaretoken': csrf_token, */ // not required for $.get()
                'begin' : so_far,
            };
            $.get("context/collection/", $data, function(result) {
                $( result ).appendTo( "#collection_song_items" );
            });
    }

    this.append_to_playlist = function() {
        /* $(this) is expected to be a collection song item */
        var $playlist_id = $(this).attr("data-playlist_id");
        var $song_id = $(this).attr("data-song_id");
        var $data = {
            'csrfmiddlewaretoken': csrf_token,
            'playlist_id' : $playlist_id,
            'song_id': $song_id,
        };
        /* update number of playlist items in sidebar */
        // TODO: increase *only* number of playlist items in sidebar
        $( "#sidebar_playlists_content" ).load("playlist/append/", $data, function() {
            sidebar.bind();
        });
        return false; // don't do anything else
    }
}

