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
        var $data = {
            'csrfmiddlewaretoken': csrf_token
        };
        $(this).append("<img class='spinner'  height='18' width='18' src='static/css/spinner.gif' />");
        $( "#context_container" ).load("context/collection/", $data, function() {
            collection.bind();
            $( "#sidebar" ).find( ".spinner" ).fadeOut(500);
        });
    }

    this.show_playlist = function() {
        var $data = {
            'csrfmiddlewaretoken': csrf_token,
            'playlist_id': $(this).attr("data-playlist_id"),
        };
        $(this).append("<img class='spinner'  height='18' width='18' src='static/css/spinner.gif' />");
        $( "#context_container" ).load("context/playlist/",  $data, function() {
            playlist.bind(); // for drag n drop
            $("#sidebar").find(".spinner").fadeOut(500);
        });

        return false; // Don't do anything else
    }

    this.show_upload = function() {
        var $data = {
            'csrfmiddlewaretoken': csrf_token
        };
        $(this).append("<img class='spinner'  height='18' width='18' src='static/css/spinner.gif' />");
        $( "#context_container" ).load("context/upload/", $data, function() {
            upload.bind(); // for eventually uploads in progress
            $("#sidebar").find(".spinner").fadeOut(500);
        });
    }
    this.show_download = function() {
        var $data = {
            'csrfmiddlewaretoken': csrf_token
        };
        $(this).append("<img class='spinner'  height='18' width='18' src='static/css/spinner.gif' />");
        $( "#context_container" ).load("context/download/", $data, function() {
            download.bind(); // for eventually uploads in progress
            $("#sidebar").find(".spinner").fadeOut(500);
        });
    }
}

