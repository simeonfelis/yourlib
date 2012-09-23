function Collection() {
    this.bind = function(){

        collection.update_viewport();

        $("#songs_count").remove();

        $( ".song_item" ).draggable({
            items: "li:not(.song_item_heading, :not(.song_info))",
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
    this.bind_filter_artists = function(by_who) {
        if (by_who) {
            console.log("bind_filter_artists by", by_who);
        }
        else {
            console.log("bind_filter_artists by unknown");
        }
        $("#selectionArtist").bind("change", function(){
            var artists = new Array();
            $(this).find("option:selected").each(function(){
                artists.push($(this).attr("value"));
            });
            console.log("triggered post for filter selectionArtist");
            $.post("filter/artists/", {'artists[]': artists}, function(data){
                console.log("made post for filter selectionArtist");
                var songs = $(data).find("#songs");
                var albums = $(data).find("#selectionAlbum");
                $("#songs").remove();
                $("#context_collection_songs_container").append(songs);
                $("#selectionAlbum").remove();
                $("#context_collection_filter_albums").append(albums);
                //collection.bind_filter_artists("after post filter artists");
            });
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

    this.filter_genre = function() {
        var genre_id = $(this).attr("data-genre_id");
        $("#collection_browser_songs_container").load("filter/set/genre/", {'genre_id': genre_id}, function() {
            console.log("genre filter set");
        });
    }

    this.song_play = function() {
        var $data = {
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
            collection.bind_filter_artists("collection search");
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
                collection.bind_filter_artists("toggle_filter");
            });
        }
        else {
            $(this).html("Show filter");
            $("#context_collection_filter").slideUp("slow", function(){
                $(this).remove();
                /* tell server we hid the filter. he maybe wants to clear/save states */
                $.post("context/filter/", {'filter_show': false}, function(){
                    console.log("hid filter");
                });
            });
        }
    }

    /* Will exhibit already fetched content data (collection.content)
     * Parameter data will set the (new or initial) content data.
     */
    this.exhibit = function(data) {
        if (data) {
            collection.content = data;
        }
        if ($("#context_container").find("#context_content").length > 0) {
            $("#context_content").fadeOut(200, function() {
                $("#context_container").append($(collection.content).fadeIn(500));
                $(this).remove();
                collection.bind();
            });
        }
        else {
            $("#context_container").append($(collection.content).fadeIn(500));
        }
    }

    this.update_viewport = function() {
        var height = context_content.height - $("#context_header").height() - 1;
        $("#context_collection_container").height( height );

        $(".song_items .mime").width(35);
        $(".song_items .track").width(20);
        var width = context_content.width - 83; // leave 2px to avoid line wrap on some browsers, 25px for scrollbar
        $(".song_items .artist").width(width*0.24);
        $(".song_items .title" ).width(width*0.24);
        $(".song_items .album" ).width(width*0.24);
        $(".song_items .genre" ).width(width*0.24);
    }
}

