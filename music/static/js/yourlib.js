
/* yourlib common stuff, find context specific stuff in subsequent yourlib_<files>.js  */

function highlight_playing() {

    $( ".currently_playing" ).removeClass("currently_playing", 500);

    var playlist_id = $( "#player1" ).attr("data-playlist_id");
    var item_id     = $( "#player1" ).attr("data-item_id");
    var song_id     = $( "#player1" ).attr("data-song_id");

    if (playlist_id != 0) {
        // create selector for playlist item
        var sel = '#playlist_' + playlist_id + "_item_" + item_id;
        $( sel ).addClass("currently_playing", 500);
    }
    else {
        // create selector for collection song
        var sel = '#collection_song_id_' + song_id;
        $( sel ).addClass("currently_playing", 500);
    }
}

function Player() {
    this.next = function() {
        this.event_ended();
    }

    this.event_ended = function() {
        $.post("play/next", {"csrfmiddlewaretoken": csrf_token}, function(song_info) {
            if (song_info=="") {
                return;
            }
            else {
                this.play_song(song_info);
            }
        });
    };

    this.play_song = function(song_info) {

        $( "#player1_song_info_title" ).html(song_info.title);
        $( "#player1_song_info_artist" ).html(song_info.artist);

        /* rebuild player (maybe firefox issue on invalid sources?) */
        $( "#player1" ).remove();
        $('<audio id="player1" controls="controls" preload="auto"></audio>').appendTo("#player1_temp");

        /* set src url */
        var $song_url='play/song/' + song_info.song_id;
        if (song_info.mime == "audio/ogg") {
            $('<source id="player1_ogg_source" src="' + $song_url + '" type="audio/ogg"></source>').appendTo("#player1");
        }
        else if (song_info.mime == "audio/mp3") {
            $('<source id="player1_mp3_source" src="' + $song_url + '" type="audio/mp3"></source>').appendTo("#player1");
        }
        $( "#player1" ).bind("ended", this.event_ended);
        $( "#player1" )[0].pause();
        $( "#player1" )[0].load();
        $( "#player1" )[0].play();
        // maybe this should be just defined globally
        $( "#player1" ).attr("data-playlist_id", song_info['playlist_id']);
        $( "#player1" ).attr("data-item_id", song_info['item_id']);
        $( "#player1" ).attr("data-song_id", song_info['song_id']);

        highlight_playing();
    }
}

function Yourlib() {
    this.logout = function() {
        var $data = {
            'csrfmiddlewaretoken': csrf_token,
        };
        $.post("accounts/logout/", $data, function() {
            window.location = "";
        });
    }
    this.rescan = function() {
        $( "#rescan_status" ).html("Rescan requested. This might take a while....");

        var data = {"csrfmiddlewaretoken": csrf_token, "playlist_name": $(this).val()};
        $.post("rescan", data, function(rescan_status) {
            yourlib.check_scan_status();
        })
        .success()
        .error(function() { $( "#rescan_status" ).html("Status not yet available..."); });
        return false; // don't do anything else
    }

    this.check_scan_status = function() {
        $.get("rescan", function(rescan_status) {
            $( "#rescan_status" ).html("Status: " + rescan_status);
            if ((rescan_status != "idle") && (rescan_status != "error")) {
                this.bind_check_scan_timeout();
            }
        });
        return false;
    }
    this.bind_check_scan_timeout = function() {
        setTimeout(this.check_scan_status, 5000);
    }
}

function Upload() {
    this.bind = function() {
        // check if there are uploads ongoing
        if ($("li", "#upload_status_content" ).length != 0 ) {
            console.log("bind: uploads in progress");
            this.bind_check_status_timeout();
        }
        else
            console.log("bind: NO uploads in progress");
    }
    this.bind_check_status_timeout = function() {
        setTimeout(this.check_status, 1000);
    }
    this.check_status = function() {
        $( "#upload_status_content" ).load("upload/", function() {
            // attention: we are now not in Upload, but document.window!
            if ($("li", "#upload_status_content" ).length != 0) {
                console.log("check_status: uploads in progress");
                upload.bind_check_status_timeout();
            }
            else
                console.log("check_status: NO uploads in progress");
        });
    }
}


$(document).ready(function () {

    /*
     * Global variables. They are available without the window namespace, too.
     */
    window.player1 = new Player();
    window.yourlib = new Yourlib();
    window.collection = new Collection();
    window.playlist = new Playlist();
    window.upload = new Upload();
    window.sidebar = new Sidebar(); // must be last?

    /*
     * Event delegation. They will work globally on dynamic content, too.
     * Events and functionality that cannot be bind like that, must be bound
     * manually with <object>.bind(), e.g. sidebar.bind()
     */

    $(document).on("mouseenter", ".collection_add_to", function() { $(this).find( ".playlists" ).fadeIn("fast"); });
    $(document).on("mouseleave", ".collection_add_to", function() { $(this).find( ".playlists" ).fadeOut("fast"); });

    /* global header */
    $(document).on("click",  "#logout",                   yourlib.logout);
    $(document).on("click",  "#btn_rescan_library",       yourlib.rescan);

    /* player */
    $(document).on("click",  "#btn_player1_next",         player1.next);

    /* sidebar */
    $(document).on("click",  "#btn_context_collection",   sidebar.show_collection);
    $(document).on("click",  ".btn_sidebar_playlist",     sidebar.show_playlist);
    $(document).on("click",  "#btn_context_upload",       sidebar.show_upload);
    $(document).on("submit", "#playlist_create",          playlist.create);

    /* playlist */
    $(document).on("click",  ".btn_playlist_item_play",   playlist.item_play);
    $(document).on("click",  ".btn_playlist_item_remove", playlist.item_remove);
    $(document).on("click",  ".btn_playlist_delete",      playlist.delete_list);

    /* collection */
    $(document).on("submit", "#context_collection_search", collection.search);
    $(document).on("click",  ".btn_collection_play_song",  collection.song_play);
    $(document).on("click",  ".btn_collection_append_to_playlist", collection.append_to_playlist);
    $(document).on("click",  "#get_more_results",          collection.get_more_results);
    $(document).on("appear", "#get_more_results",          collection.get_more_results, {one: false});

    /* check document state, maybe there are ongoing actions in progress */
    if ( $( "#rescan_status" ).html() != "" ) {
        yourlib.check_scan_status();
    }

});

