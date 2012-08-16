
/* yourlib common stuff, find context specific stuff in subsequent yourlib_<files>.js  */

function highlight_playing(by_who, target) {

    if (by_who) {
        console.log("highligth_playling by", by_who);
    }
    else {
        console.log("highlight_playling by unknown");
    }

    var playlist_id = $( "#player1" ).attr("data-playlist_id");
    var item_id     = $( "#player1" ).attr("data-item_id");
    var song_id     = $( "#player1" ).attr("data-song_id");

    if (playlist_id != 0) {
        // eventually update sidebar; create selector for sidebar playlist item
        var sb_sel = '#sidebar_playlist_' + playlist_id;
        if ( ! $( sb_sel ).hasClass("currently_playing") ) {
            $( "#sidebar" ).find( ".currently_playing" ).removeClass("ui-state-highlight");
            $( "#sidebar" ).find( ".currently_playing" ).addClass("ui-state-default");
            $( "#sidebar" ).find( ".currently_playing" ).removeClass("currently_playing");
            $( sb_sel ).removeClass("ui-state-default");
            $( sb_sel ).addClass("currently_playing");
            $( sb_sel ).addClass("ui-state-highlight");
        }
        // create selector for playlist item
        var sel = '#playlist_' + playlist_id + "_item_" + item_id;
    }
    else {
        // create selector for collection song
        var sel = '#collection_song_id_' + song_id;

        // remove highlighting from playlist
        $( "#sidebar" ).find( ".currently_playing" ).removeClass("ui-state-highlight");
        $( "#sidebar" ).find( ".currently_playing" ).addClass("ui-state-default");
        $( "#sidebar" ).find( ".currently_playing" ).removeClass("currently_playing");
        $( "#btn_context_collection" ).removeClass("ui-state-default");
        $( "#btn_context_collection" ).addClass("currently_playing");
        $( "#btn_context_collection" ).addClass("ui-state-highlight");
    }

    if ( $( sel ).hasClass("currently_playing") ) {
        // don't re-apply
    }
    else {
        $( "#context_content" ).find( ".currently_playing" ).removeClass("ui-state-highlight");
        $( "#context_content" ).find( ".currently_playing" ).addClass("ui-state-default");
        $( "#context_content" ).find( ".currently_playing" ).removeClass("currently_playing");
        $( sel ).removeClass("ui-state-default");
        $( sel ).addClass("currently_playing");
        $( sel ).addClass("ui-state-highlight");
    }
}

function Player() {
    this.next = function() {
        player1.event_ended();
    }

    this.event_ended = function() {
        $.post("play/next", {"csrfmiddlewaretoken": csrf_token}, function(song_info) {
            if (song_info=="") {
                return;
            }
            else {
                player1.play_song(song_info);
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
        //if (song_info.dbg_file_path) {
        //    /* for debugging on localhost, I use a this to emulate x-accel-redirects */
        //    var $song_url='http://localhost:8080' + song_info.dbg_file_path;
        //}
        //else {
            var $song_url='play/song/' + song_info.song_id;
        //}


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

        highlight_playing("Player.play_song()", target="#content");
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
        if ($( "#btn_rescan_library" ).html() == "Cancel") {

            $( "#dialog-confirm" ).dialog({
                resizable: true,
                height:300,
                width:400,
                modal: true,
                buttons: {
                    "Continue Rescan": function() {
                        $( this ).dialog( "close" );
                    },
                    "Cancel Rescan": function() {

                        $( "#rescan_status" ).html("Cancel requested...");
                        var data = {"csrfmiddlewaretoken": csrf_token, "cancel": true};
                        $.post("rescan", data, function(rescan_status) {
                            yourlib.check_scan_status();
                        })
                        .success()
                        .error(function() { $( "#rescan_status" ).html("Server Error?"); });

                        $( this ).dialog( "close" );
                    }
                }
            });
        }
        else{
            $("#btn_rescan_library").html("Cancel");
            $( "#rescan_status" ).html("Rescan requested. This might take a while....");

            var data = {"csrfmiddlewaretoken": csrf_token};
            $.post("rescan", data, function(rescan_status) {
                yourlib.check_scan_status();
            })
            .success()
            .error(function() { $( "#rescan_status" ).html("Server Error?"); });
        }
        return false; // don't do anything else
    }

    this.check_scan_status = function() {
        $.get("rescan", function(rescan_status) {
            $( "#rescan_status" ).html("Status: " + rescan_status);
            if ((rescan_status != "idle") && (rescan_status != "error") && (rescan_status != "")) {
                $("#btn_rescan_library").html("Cancel");
                yourlib.bind_check_scan_timeout();
            }
            else {
                $("#btn_rescan_library").html("Rescan");
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

var bar = $('.bar');
var percent = $('.percent');
var status = $('#status');


$('#upload_form').ajaxForm({
    //data: {"csrfmiddlewaretoken": csrf_token},
    beforeSend: function() {
        this.url = "upload/?";
        console.log("beforeSend");
        status.empty();
        var percentVal = '0%';
        bar.width(percentVal)
        percent.html(percentVal);
    },
    uploadProgress: function(event, position, total, percentComplete) {
        console.log("uploadProgress", percentComplete);
        var percentVal = percentComplete + '%';
        bar.width(percentVal)
        percent.html(percentVal);
    },
    complete: function(xhr) {
        console.log("complete", xhr.responseTest);
        status.html(xhr.responseText);
    }
}); 


        // check if there are uploads ongoing
        if ($("li", "#upload_status_content" ).length != 0 ) {
            console.log("bind: uploads in progress");
            this.bind_check_status_timeout();
        }
        else
            console.log("bind: NO uploads in progress");
    }
    this.upload = function(event) {
        /* don't do a normal submit */
        //event.preventDefault();

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

function Download() {
    this.bind = function() {
    }
}


$(document).ready(function () {

    /*
     * Global variables. They are available without the window namespace, too.
     */
    window.player1     = new Player();
    window.yourlib     = new Yourlib();
    window.collection  = new Collection();
    window.playlist    = new Playlist();
    window.upload      = new Upload();
    window.download    = new Download();
    window.sidebar     = new Sidebar(); // must be last?
    collection.bind();
    playlist.bind();
    sidebar.bind();

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
    $(document).on("click",  "#btn_context_download",     sidebar.show_download);
    $(document).on("submit", "#playlist_create",          playlist.create);

    /* playlist */
    $(document).on("click",  ".btn_playlist_item_play",   playlist.item_play);
    $(document).on("click",  ".btn_playlist_item_remove", playlist.item_remove);
    $(document).on("click",  ".btn_playlist_delete",      playlist.delete_list);
    $(document).on("click",  ".btn_playlist_download",    playlist.download);

    /* collection */
    $(document).on("submit", "#context_collection_search", collection.search);
    $(document).on("click",  ".btn_collection_play_song",  collection.song_play);
    $(document).on("click",  ".btn_collection_append_to_playlist", collection.append_to_playlist);
    $(document).on("click",  "#get_more_results",          collection.get_more_results);
    $(document).on("appear", "#get_more_results",          collection.get_more_results, {one: false});


    /* upload */
    //$(document).on("submit", "#upload_form",               upload.upload);
//    $("body").bind("ajaxSend", function(elm, xhr, s){
//       if (s.type == "POST") {
//          xhr.setRequestHeader('X-CSRF-Token', csrf_token);
//       }
//    });
jQuery(document).ajaxSend(function(event, xhr, settings) {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    function sameOrigin(url) {
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }
    function safeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    }
});
    /* some global ui theming */
    $(".btn").on("mouseenter", function(){$(this).removeClass("ui-state-default").addClass("ui-state-focus")});
    $(".btn").on("mouseleave", function(){$(this).removeClass("ui-state-focus").addClass("ui-state-default")});

    /* check document state, maybe there are ongoing actions in progress */
    if ( $( "#rescan_status" ).html() != "" ) {
        yourlib.check_scan_status();
    }

});

