function Sidebar() {
    this.bind = function() {
        console.log("rebinding sidebar");

        $(".btn_sidebar_playlist").droppable( {
            accept: ".song_item, .btn_browse_artist",
            activeClass: "ui-state-focus",
            hoverClass: "ui-state-highlight",
            drop: sidebar.on_item_dropped_playlist,
        });

        highlight_playing(by_who='sidebar.bind', target="#sidebar");
    }

    this.on_item_dropped_playlist = function(event, ui) {
        var source = $(ui.helper).attr("data-source");
        var playlist_id = $(this).attr("data-playlist_id");

        if ("browse" == source) {
            var column = $(ui.helper).attr("data-column");

            if ("artist" == column) {
                var artist_id = $(ui.helper).attr("data-artist_id");
                playlist.append(playlist_id, artist_id, column);
            }
        }
        else if ("collection" == source) {
            song_id = $(ui.helper).attr("data-song_id");

            playlist.append(playlist_id, song_id, source);
        }
    }

    this.show_collection = function() {
        spinner_start($(this));
        $.post("collection/", {}, function(data) {
            spinner_stop( "#sidebar" );
            $("#sidebar").find(".currently_shown").removeClass("currently_shown");
            $("#btn_context_collection").addClass("currently_shown");
            collection.exhibit(data);
        });

        return false; // Don't do anything else
    }

    this.show_browse = function() {
        spinner_start($(this));
        $.post("collection/browse/", {}, function(data) {
            spinner_stop( "#sidebar");
            browse.exhibit(data);
            $("#sidebar").find(".currently_shown").removeClass("currently_shown");
            $("#btn_sidebar_browse").addClass("currently_shown");
        });
    }

    this.show_playlist = function() {
        var playlist_id = $(this).attr("data-playlist_id");
        playlist.id = playlist_id;

        spinner_start($(this));

        $.post("playlist/",  {'playlist_id': playlist_id}, function(data) {
            playlist.exhibit(data);
            playlist.bind(); // for drag n drop
            spinner_stop("#sidebar");
            $("#sidebar").find(".currently_shown").removeClass("currently_shown");
            $("#sidebar_playlist_" + playlist.id).addClass("currently_shown");
        });

        return false; // Don't do anything else
    }

    this.show_upload = function() {
        $(this).append("<img class='spinner'  height='18' width='18' src='static/css/spinner.gif' />");
        $( "#context_container" ).load("sidebar/show/upload/", {}, function() {
            upload.bind(); // for eventually uploads in progress
            $("#sidebar").find(".spinner").fadeOut(500);
        });
    }
}

