function Sidebar() {
    this.bind = function() {
        console.log("rebinding sidebar");

        $(".btn_sidebar_playlist").droppable( {
            accept: ".song_item, .btn_browse_artist, .btn_browse_album, .btn_browse_title, .btn_browse_genre",
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
            var item_id = $(ui.helper).attr("data-item_id");
            playlist.append(playlist_id, item_id, column);
        }
        else if ("collection" == source) {
            item_id = $(ui.helper).attr("data-song_id");

            playlist.append(playlist_id, item_id, source);
        }
    }

    this.show_collection = function() {

        spinner_start($(this));
        collection.exhibit(function() {spinner_stop( "#sidebar");});

        return false; // Don't do anything else
    }

    this.show_browse = function() {
        spinner_start($(this));
        browse.exhibit(function() {spinner_stop( "#sidebar");})
    }

    this.show_playlist = function() {
        playlist_id = $(this).attr("data-playlist_id");
        //playlist.id = playlist_id;

        spinner_start($(this));
        playlist.exhibit(playlist_id, function() {spinner_stop( "#sidebar");})

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

