

function Collection() {
    this.bind = function(){

   $(function(){
        $('#songs').scrollPagination({
            'contentPage': 'collection/songs/', // the url you are fetching the results
            'contentData': {"so_far": function() {return $(".song_item").length;}}, // these are the variables you can pass to the request, for example: children().size() to know which page you are
            'scrollTarget': $("#context_collection_container"), // who gonna scroll? in this example, the full window
            'appendTarget': $("#collection_song_items"),
            'heightOffset': 10, // it gonna request when scroll is 10 pixels before the page ends
            'beforeLoad': function(){ // before load function, you can display a preloader div
                console.log("pagination befor load");
                $('#loading').fadeIn();
            },
            'afterLoad': function(elementsLoaded){ // after loading content, you can use this function to animate your new elements
                console.log("pagination after load");
                 $('#loading').fadeOut();
                 //var i = 0;
                 //$(elementsLoaded).fadeInWithDelay();
                 //if ($('#song_items').children().size() > 100){ // if more than 100 results already loaded, then stop pagination (only for testing)
                 //   $('#nomoreresults').fadeIn();
                 //   $('#song_items').stopScrollPagination();
                 //}
                 collection.update_viewport();
            }
        });

        // code for fade in element by element
        $.fn.fadeInWithDelay = function(){
            console.log("pagination fadeInWith delay");
            var delay = 0;
            return this.each(function(){
                $(this).delay(delay).animate({opacity:1}, 200);
                delay += 100;
            });
        };
    });



        $("#songs_count").remove();

        $( ".song_item" ).draggable({
            items: "li:not(.song_item_heading, :not(.song_info))",
            helper: function(event) {
                artist = $(this).find(".artist").html();
                title = $(this).find(".title").html();
                song_id = $(this).attr("data-song_id");
                console.log("Dragging element with song id " + song_id)

                helper = $("<div class='ui-widget-content ui-state-focus ui-corner-all'></div>");
                helper.html(artist + " - " + title);

                helper.attr("data-song_id", song_id);
                helper.attr("data-source", "collection");
                return $( helper );
            },
            appendTo: "body",
            containment: "document",
            revert: "invalid",
            delay: 100,
        });
        $( ".song_item").disableSelection();

        collection.update_viewport();

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
        $( "#context_collection_songs_container").load("collection/search/", $data, function(response, status, xhr) {
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
            $("#context_content").fadeOut(300, function() {
                $("#context_container").append($(collection.content).fadeIn(500));
                collection.bind();
                $(this).remove();
            });
        }
        else {
            $("#context_container").append($(collection.content).fadeIn(500));
            collection.bind();
        }
    }

    this.update_viewport = function() {
        if ($.find("#context_collection_container").length == 0) {
            console.log("collection.update_viewport: nothing to update");
            return;
        }
        context_content.update_viewport();
        var height = context_content.height - $("#context_header").height() - 1;
        $("#context_collection_container").height( height );

        $(".song_items .mime").width(35);
        $(".song_items .track").width(20);
        var tmpWidth = context_content.width - 83; // leave 2px to avoid line wrap on some browsers, 25px for scrollbar
        var bla = tmpWidth*0.25;
        var blu = tmpWidth*0.15;
        $(".song_items .artist").width(bla);
        $(".song_items .title" ).width(bla);
        $(".song_items .album" ).width(bla);
        $(".song_items .genre" ).width(blu);
    }
}

