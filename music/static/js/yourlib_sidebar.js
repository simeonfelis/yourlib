function Sidebar() {
    this.bind = function() {
        console.log("rebinding sidebar");

        $(".btn_sidebar_playlist").droppable( {
            accept: ".song_item",
            activeClass: "ui-state-default",
            hoverClass: "ui-state-highlight",
            drop: function(event, ui) {
                song_id = $(ui.draggable).attr("data-song_id");
                playlist_id = $(this).attr("data-playlist_id");

                playlist.append(playlist_id, song_id);
            },
        });
    }

    this.show_collection = function() {
        var $data = {
            'csrfmiddlewaretoken': csrf_token
        };
        $( "#context_container" ).load("context/collection/", $data, function() {
            collection.bind();
        });
    }

    this.show_playlist = function() {
        var $data = {
            'csrfmiddlewaretoken': csrf_token,
            'playlist_id': $(this).attr("data-playlist_id"),
        };
        $( "#context_container" ).load("context/playlist/",  $data, function() {
            playlist.bind(); // for drag n drop
        });

        return false; // Don't do anything else
    }

    this.show_upload = function() {
        var $data = {
            'csrfmiddlewaretoken': csrf_token
        };
        $( "#context_container" ).load("context/upload/", $data, function() {
            upload.bind(); // for eventually uploads in progress
        });
    }
    this.show_download = function() {
        var $data = {
            'csrfmiddlewaretoken': csrf_token
        };
        $( "#context_container" ).load("context/download/", $data, function() {
            download.bind(); // for eventually uploads in progress
        });
    }
}

