

function Collection() {

    // init (constructor) at end of function

    this.bind = function(){

        // bind existing items
        this.bindSongElements($("#context_collection .song_item"));

        // search submit
        $("#context_collection_search").on("submit", this.search);

        // pagination
        this.bindPagination();
    }

    this.highlight = function() {
        $(this).addClass("ui-state-hover");
    }
    this.unlight = function() {
        $(this).removeClass("ui-state-hover");
    }

    this.bindPagination = function() {

        this.songPagination = new Pagination({
            scrollTarget : '#context_collection_container',
            appendTarget : "#collection_song_items",
            contentUrl   : base_url + "collection/",
            contentData  : function() {return $(".song_item").length;},
            beforeLoad   : this.paginationStart,
            afterLoad    : this.paginationDone,
            errorLoad    : this.paginationError,
            enabled      : true
        });

    }

    this.bindSongElements = function(elements) {
        console.log("============ Collection bindSongElements =============");
        $( elements )
        .on("click", this.song_play)
        .draggable({
            items: "li:not(.song_item_heading, :not(.song_info))",
            helper: function(event) {
                artist = $(this).find(".artist").html();
                title = $(this).find(".title").html();
                song_id = $(this).attr("data-song_id");

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
        })
        .disableSelection()
        .off("mouseenter", this.highlight)
        .off("mouseleave", this.unlight)
        .on("mouseenter",  this.highlight)
        .on("mouseleave",  this.unlight);
    }

    this.paginationDone = function(newData) {
        if ($(newData).length > 0) {
            $('#loading_collection').fadeOut();
            collection.bindSongElements(newData);
            collection.update_viewport();
        }
        else {
            $('#loading_collection').html("No more data");
            $('#loading_collection').fadeOut();
        }
    }
    this.paginationStart = function() {
        $('#loading_collection').fadeIn();
    }

    this.paginationError = function(jqXHR, status, error) {
        $('#loading_collection').html(status + " " + error);
        $('#loading_collection').fadeIn("fast", function() {
            $(this).fadeOut("slow");
        });
    }

    this.song_play = function() {
        var $data = {
            'song_id': $(this).attr("data-song_id"),
            'source' : 'collection',
        };
        url = base_url + "collection/search/"
        $.post(url, $data, function(song_info) {
            player1.play_song(song_info);
        });
        return false;
    }

    this.search = function(e) {

        e.preventDefault();

        $( "#context_collection_search_status" ).html("Started");
        var data = {
            "search_terms": $( "#collection_search_terms" ).val(),
        };

       var url = base_url + "collection/search/";

        $.ajax({
            type:     "POST",
            url:      url,
            data:     data,
            success:  function(data, status, jqXHR) {
                // we are in context window again. sigh.
                collection.new_context = $(data).find("#context_collection");

                $("#context_collection").fadeOut("fast", function() {
                    $(this).replaceWith(collection.new_context).fadeIn("fast");
                    collection.bind();
                    collection.update_viewport();
                });
            },
            error:    function(jqXHR, status, error) {
                // we are in context window again. sigh.
                $( "#context_collection_search_status" ).html(status + " " + error);
            },
            datatype: "html"
        });

        return false; // Don't do anything else
    }

    this.exhibit = function(exhibit_finished_cb) {

        this.exhibit_finished = exhibit_finished_cb;

        is_loaded = $("#context_collection").length > 0;

        if (is_loaded) {
            $("#context_content").children().fadeOut("fast");
            $("#context_content").children().promise().done(function() {
                $("#context_collection").fadeIn("fast", function() {
                    collection.exhibit_finished();
                });
                collection.update_viewport();
                highlight_playing("collection.exhibit()", "#context_collection");
            });
        }
        else {

            var data = {};

            var url = base_url + "collection/";

            $.ajax({
                type:     "GET",
                url:      url,
                data:     data,
                success:  function(data, status, jqXHR) {
                    // we are in context window again. sigh.

                    $("#sidebar").find(".currently_shown").removeClass("currently_shown");
                    $("#sidebar_show_collection").addClass("currently_shown");

                    collection.view = $(data).find("#context_collection");

                    $("#context_content").children().fadeOut("slow");
                    $("#context_content").children().promise().done(function() {
                        $("#context_content").append($(collection.view).fadeIn("slow", function() {
                            collection.exhibit_finished();
                        }));
                        collection.update_viewport();
                        highlight_playing("collection.exhibit()", "#context_collection");
                        collection.bind();
                    });


                },
                error:    function(jqXHR, status, error) {
                    // we are in context window again. sigh.
                    console.log("ERROR SHOWING COLLECTION");
                },
                complete:    function(jqXHR, textStatus) {
                },
                datatype: "html"
            });
        }
    }

    this.update_viewport = function() {

        console.log("============ Collection update_viewport =============");


        if ($.find("#context_collection_container").length == 0) {
            console.log("collection.update_viewport: nothing to update");
            return;
        }

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

    console.log("============ Collection init =============");

    this.bind();
    this.update_viewport();

}

