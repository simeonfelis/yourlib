function Sidebar() {
    this.bind = function() {
        console.log("rebinding sidebar");

        $(".btn_sidebar_playlist").droppable( {
            accept: ".song_item",
            activeClass: "ui-state-focus",
            hoverClass: "ui-state-highlight",
            drop: function(event, ui) {
                song_id = $(ui.draggable).attr("data-song_id");
                playlist_id = $(this).attr("data-playlist_id");

                playlist.append(playlist_id, song_id);
            },
        });

        highlight_playing(by_who='sidebar.bind', target="#sidebar");
    }

    this.show_collection = function() {
        spinner_start($(this));
        $.post("collection/", {}, function(data) {
            collection.exhibit(data);
            spinner_stop( "#sidebar" );
            $("#sidebar").find(".currently_shown").removeClass("ui-widget-header");
            $("#sidebar").find(".currently_shown").addClass("ui-widget-content");
            $("#sidebar").find(".currently_shown").removeClass("currently_shown");
            $("#btn_context_collection").addClass("ui-widget-header");
            $("#btn_context_collection").addClass("currently_shown");
        });

        return false; // Don't do anything else
    }

    this.show_playlist = function() {
        var playlist_id = $(this).attr("data-playlist_id");
        playlist.id = playlist_id;

        spinner_start($(this));

        $.post("playlist/",  {'playlist_id': playlist_id}, function(data) {
            playlist.exhibit(data);
            playlist.bind(); // for drag n drop
            spinner_stop("#sidebar");
            $("#sidebar").find(".currently_shown").removeClass("ui-widget-header");
            $("#sidebar").find(".currently_shown").addClass("ui-widget-content");
            $("#sidebar").find(".currently_shown").removeClass("currently_shown");

            $("#sidebar_playlist_" + playlist.id).addClass("ui-widget-header");
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

