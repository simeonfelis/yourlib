function Collection() {
    this.bind = function(){

        $("#songs_count").remove();

        $( ".song_item" ).draggable({
            helper: function(event) {
                artist = $(this).find(".artist").html();
                title = $(this).find(".title").html();
                song_id = $(this).attr("data-song_id");
                console.log("Dragging element with song id " + song_id)
                helper = $("<div class='ui-widget-content ui-state-focus ui-corner-all'></div>");
                helper.attr("data-song_id", song_id);
                helper.html(artist + " - " + title);
                return $( helper );
            },
            appendTo: "body",
            containment: "document",
            revert: "invalid",
            delay: 100,
        });
        $( ".song_item").disableSelection();

        highlight_playing("Collection.bind()", target="#context_container");
    }
    this.bind_filter = function() {
        $("#selectionArtist").bind("change", function(){
            var artists = new Array();
            $(this).find("option:selected").each(function(){
                artists.push($(this).attr("value"));
            });
            if ( artists.length > 0 ) {
                // make filter
                $( "#context_collection_songs_container" ).load("filter/artists/", {'artists[]':artists}, function() {
                    //alert("query albums");
                    collection.bind_filter();
                })
            }
        });
        $("#selectionAlbum").bind("change", function(){
            var albums = new Array();
            $(this).find("option:selected").each(function(){
                albums.push($(this).attr("value"));
            });
            if ( albums.length > 0 ) {
                // query filter
                $( "#context_collection_songs_container" ).load("filter/albums/", {'albums[]':albums}, function() {
                    //alert("query albums");
                    collection.bind_filter();
                })
            }
        });
    }

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
        $( "#context_collection_songs_container").load("search/", $data, function(response, status, xhr) {
            if (status == "error") {
                $( "#context_collection_search_status" ).html("Error " + xhr.status + " " + xhr.statusText);
            }
            else {
                var count = $("#songs_count").html();
                $("#songs_count").remove();
                $( "#context_collection_search_status" ).html("Finished (" + count + ")");
            }
            collection.bind();
            collection.bind_filter();
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
                if (result != "") {
                    $( result ).appendTo( "#collection_song_items" );
                    collection.bind();
                }
            });
    }

    this.toggle_filter = function() {
        if ( $(this).html() == "Show filter" ) {
            $(this).html("Hide filter");
            $( "#context_collection_filter_container" ).load("context/filter/", {'filter_show': true}, function() {
                collection.bind_filter();
            });
        }
        else {
            $(this).html("Show filter");
            $("#context_collection_filter").slideUp("slow", function(){
                $(this).remove();
                /* tell server we hid the filter. he maybe wants to clear/save states */
                $.post("context/filter/", {'filter_show': false});
            });
        }
    }
}

