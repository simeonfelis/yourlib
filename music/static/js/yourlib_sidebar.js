function Sidebar() {

    // init (constructor) is at the end of this function

    this.bind = function() {

        console.log("============ Sidebar bind =============");

        //highlight_playing('sidebar.bind()', "#sidebar");

        $("a").button().find(".ui-button-text").removeClass("ui-button-text"); // 'a' are looking ugly when they are used as jquery buttons. this is a workaround

        // make sure click handlers are only mapped once
        //$("#sidebar").off("click", "a", this.show_shares_playlist);

        //$("#sidebar").on("click", )
        //$("#sidebar_shares").on("click",  "a", this.show_shares_playlist);

        this.bind_collection();
        this.bind_playlists();
        this.bind_shares();

    }

    this.bind_collection = function() {
        console.log("============ Sidebar bind_collection =============");

        $("#sidebar_show_collection").on("click",  function(event) {
            event.preventDefault();
            var stateObj = null; var title = "";
            var url = $(this).attr("href");
            history.pushState(stateObj, title, url);
            spinner_start($(this));
            collection.exhibit(
                function() {spinner_stop( "#sidebar");}
            );
        }
        );
        $("#sidebar_show_collection_browse").on("click",  function(event) {
            event.preventDefault();
            var stateObj = null; var title = "";
            var url = $(this).attr("href");
            history.pushState(stateObj, title, url);
            spinner_start($(this));
            browse.exhibit(function() {spinner_stop( "#sidebar");})
        });
    }

    this.bind_playlists = function() {
        console.log("============ Sidebar bind_playlists =============");

        this.bind_playlist_items();

        $("#playlist_create").on("submit", playlist.create);

    }

    this.bind_playlist_items = function() {
        $(".btn_sidebar_show_playlist").on("click", function() {
            playlist_id = $(this).attr("data-playlist_id");
            event.preventDefault();
            var stateObj = null; var title = "";
            var url = $(this).attr("href");
            history.pushState(stateObj, title, url);

            spinner_start($(this));
            playlist.exhibit(playlist_id, url, function() {spinner_stop( "#sidebar");})

            return false; // Don't do anything else
        });

        $("a").button().find(".ui-button-text").removeClass("ui-button-text"); // 'a' are looking ugly when they are used as jquery buttons. this is a workaround

        $("#sidebar_playlists h2 a").droppable( {
            accept: ".song_item, .btn_browse_artist, .btn_browse_album, .btn_browse_title, .btn_browse_genre",
            activeClass: "ui-state-focus",
            hoverClass: "ui-state-highlight",
            drop: this.on_item_dropped_playlist,
        });
    }

    this.bind_shares = function() {
        console.log("============ Sidebar bind_shares =============");

        $("#sidebar_show_shares").on("click", function() {
            event.preventDefault();
            var stateObj = null; var title = "";
            var url = $(this).attr("href");
            history.pushState(stateObj, title, url);

            spinner_start($(this));
            share_view.exhibit(url, function() {spinner_stop( "#sidebar");})

            return false; // Don't do anything else
        });

        $("#sidebar_playlists h2 a").droppable( {
            accept: ".song_item, .btn_browse_artist, .btn_browse_album, .btn_browse_title, .btn_browse_genre",
            activeClass: "ui-state-focus",
            hoverClass: "ui-state-highlight",
            drop: this.on_item_dropped_playlist,
        });
    }

    this.on_item_dropped_playlist = function(event, ui) {
        var source = $(ui.helper).attr("data-source");
        var playlist_id = $(this).attr("data-playlist_id");

        if ("browse" == source) {
            var column = $(ui.helper).attr("data-column");
            var item_id = $(ui.helper).attr("data-item_id");
            playlist.append(playlist_id, item_id, column);
        }
        else if ("collection" == source) {
            item_id = $(ui.helper).attr("data-song_id");

            playlist.append(playlist_id, item_id, source);
        }
    }

    this.show_playlist = function() {
        playlist_id = $(this).attr("data-playlist_id");
        //playlist.id = playlist_id;

        spinner_start($(this));
        playlist.exhibit(playlist_id, function() {spinner_stop( "#sidebar");})

        return false; // Don't do anything else
    }

    this.show_shares = function(event) {
        event.preventDefault();
        var url = $(this).attr("href");
        $.ajax({
            type: "GET",
            url: url,
            data: {},
            success: function(data){
                var my_context_content = $(data).find("#context_shares");
                $("#context_content").children(":first").fadeOut("slow");
                $("#context_content").children(":first").promise().done(function() {
                    $("#context_content").append($(my_context_content).fadeIn("slow", function() {}));
                });
            },
            dataType: 'html'
        });
        return false; // Don't do anything else
    }

    this.show_shares_playlist = function(event) {
        event.preventDefault();
        var url = $(this).attr("href");
        var data = {
            "playlist_id": $(this).attr("data-playlist_id"),
        }
        $.ajax({
            type: "GET",
            url: url,
            data: data,
            success: function(data){
                var blu = $(data).find("#context_content");
                var bla = $(blu).children(":first");
                $("#context_content").children(":first").fadeOut("slow");
                $("#context_content").children(":first").promise().done(function() {
                    $("#context_content").append($(bla).fadeIn("slow", function() {}));
                });
            },
            dataType: 'html'
        });
        return false; // Don't do anything else
    }

    this.show_upload = function() {
        spinner_start($(this));
        upload.exhibit(function() {spinner_stop( "#sidebar")});
        //$(this).append("<img class='spinner'  height='18' width='18' src='static/css/spinner.gif' />");
    }

    this.update_viewport = function() {

        console.log("============ Sidebar update_viewport =============");

        var height = context_content.height - $("#player1_container").height() - 40;
        $("#sidebar_navi").height( height );

    }
    console.log("============ Sidebar init =============");

    this.bind();
    this.update_viewport();
}

