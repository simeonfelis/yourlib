
/* yourlib common stuff, find context specific stuff in subsequent yourlib_<files>.js  */

function spinner_start(elem) {
    $(elem).append("<img class='spinner'  height='18' width='18' src='/static/css/spinner.gif' />");
}

function spinner_stop(sel) {
    $( sel ).find( ".spinner" ).fadeOut(500);
}

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

    /* sidebar */
    if (playlist_id != 0) {
        // eventually update sidebar; create selector for sidebar playlist item
        var sb_sel = '#sidebar_playlist_' + playlist_id;
        if ( ! $( sb_sel ).hasClass("currently_playing") ) {
            $( "#sidebar" ).find( ".currently_playing" ).find(".playing_icon").remove();
            $( "#sidebar" ).find( ".currently_playing" ).removeClass("currently_playing");
            $( sb_sel ).addClass("currently_playing");
            $( sb_sel ).append("<span class='playing_icon'>♬</span>");
        }
        // create selector for playlist item
        var sel = '#playlist_' + playlist_id + "_item_" + item_id;
    }
    else {
        // create selector for collection song
        var sel = '#collection_song_id_' + song_id;

        // remove highlighting from playlist
        $( "#sidebar" ).find( ".currently_playing" ).find(".playing_icon").remove();
        $( "#sidebar" ).find( ".currently_playing" ).removeClass("currently_playing");
        $( "#btn_context_collection" ).addClass("currently_playing");
        $( "#btn_context_collection" ).append("<span class='playing_icon'>♬</span>");
    }

    /* context content. sel was created either for playlist or collection */
    if ( $( sel ).hasClass("currently_playing") ) {
        // don't re-apply
    }
    else {
        //$( "#context_content" ).find( ".currently_playing" ).find(".playing_icon");
        //$( "#context_content" ).find( ".currently_playing" ).addClass("ui-state-default");
        //$( "#context_content" ).find( ".currently_playing" ).removeClass("currently_playing");
        //$( sel ).removeClass("ui-state-default");
        //$( sel ).addClass("currently_playing");
        //$( sel ).addClass("ui-state-highlight");
    }
}


function Download() {
    this.bind = function() {
    }
}

function Browse() {

    this.bind = function() {
        this.update_viewport();

        $(".btn_browse_title").on("click", function(){
            var $data = {
                'song_id': $(this).attr("data-title_id"),
                'source' : 'collection',
            };
            $.post("play/", $data, function(song_info) {
                player1.play_song(song_info);
            });
            return false;
        });

        $(".btn").on("mouseenter", function(){$(this).removeClass("ui-state-default").addClass("ui-state-focus")});
        $(".btn").on("mouseleave", function(){$(this).removeClass("ui-state-focus").addClass("ui-state-default")});

        // select item after hover delay
        $("#browse_artist_filter .btn, #browse_album_filter .btn, #browse_genre_filter .btn").on("mouseenter", function() {
            $this = $(this);
            if ($this.hasClass("pre-selected") || $this.hasClass("pre-unselected")) {
                return;
            }
            if ($this.hasClass("selected")) {
                $this.addClass("pre-unselected");
                //$this.data('delay', setTimeout(function() {$this.removeClass("selected"); browse.on_artist_clicked()}, 900));
                $this.data('delay', setTimeout(function() {
                    var tmp = $this.parent().find(".ui-widget-header");
                    var column = tmp.html();
                    $this.removeClass("selected");
                    browse.on_column_item_clicked(column);
                }, 900));
            }
            else {
                $this.addClass("pre-selected");
                //$this.data('delay', setTimeout(function() {$this.removeClass("pre-selected").addClass("selected"); browse.on_artist_clicked()}, 900));
                $this.data('delay', setTimeout(function() {
                    var tmp = $this.parent().find(".ui-widget-header");
                    var column = tmp.html();
                    $this.removeClass("pre-selected").addClass("selected");
                    browse.on_column_item_clicked(column);
                }, 900));
            }
        });
        $("#browse_artist_filter .btn, #browse_album_filter .btn, #browse_genre_filter .btn").on("mouseleave", function() {
            $this = $(this);
            if ($this.hasClass("pre-selected") || $this.hasClass("pre-unselected")) {
                clearTimeout($this.data("delay"));
                $this.removeClass("pre-selected");
                $this.removeClass("pre-unselected");
            }
        });

    }

    this.on_column_received = function(data) {
            if ( $(data).attr('id') == "context_browse_album_container" ) {
                if ($("#context_container").find("#context_browse_album_container").length > 0) {
                    $("#context_browse_album_container").replaceWith(data);
                    browse.bind();
                }
            }
            if ( $(data).attr('id') == "context_browse_title_container" ) {
                if ($("#context_container").find("#context_browse_title_container").length > 0) {
                    $("#context_browse_title_container").replaceWith(data);
                    browse.bind();
                }
            }
    }

    this.on_column_item_clicked = function(column_from) {
        var selected = $("#browse_" + column_from + "_filter .selected").get();
        var item_ids = [];
        for (item in selected) {
            item_ids.push($(selected[item]).attr("data-" + column_from + "_id"));
        }
        var ar_name = column_from + '_ids';
        var data = {
            'items' : item_ids,
        }

        $.post('collection/browse/' + column_from + '/', data, browse.on_column_received);
    }
/*
    this.on_artist_clicked = function() {
        var selected = $("#browse_artist_filter .selected").get();
        var artist_ids = [];
        for (artist in selected) {
            artist_ids.push($(selected[artist]).attr("data-artist_id"));
        }
        var data = {
            'artist_ids'    : artist_ids,
        }

        $.post('collection/browse/artist/', data, function(data){
            // handle albums
            var tmp = $(data).find("#context_browse_album_container").get(0);
            
            if ( $(data).attr('id') == "context_browse_album_container" ) {
                if ($("#context_container").find("#context_browse_album_container").length > 0) {
                    $("#context_browse_album_container").replaceWith(data);
                    browse.bind();
                }
            }

            // handle song items
            if ($(data).find("#context_browse_song_container").length > 0) {
                // TODO
            }

        });
    }
*/
    this.exhibit = function(data) {
        if (data) {
            browse.content = data;
        }
        if ($("#context_container").find("#context_content").length > 0) {
            $("#context_content").fadeOut(200, function() {
                $("#context_container").append($(browse.content).fadeIn(500));
                $(this).remove();
                browse.bind();
            });
        }
        else {
            $("#context_container").append($(browse.content).fadeIn(500));
        }
    }

    this.update_viewport = function() {
        if ($.find("#context_browse_container").length == 0) {
            // nothing to update
            return;
        }

        var height = context_content.height - $("#context_header").height() - 1;
        $("#context_browse_artist_container").height( height );
        $("#context_browse_album_container").height( height );
        $("#context_browse_title_container").height( height );
        var width = context_content.width*0.32 - 1;
        $(".browse_column").width( width );

    }
}

function ContextContent() {
    this.update_viewport = function() {
        this.width = this.get_width();
        this.height = this.get_height();
        $("#context_container").height(this.height);
        $("#context_container").width(this.width);
    }
    this.get_width = function() {
        return $(document).width() - 300 - 20; // sidebar and paddings
    }
    this.get_height = function() {
        return $(document).height() - 50 - 20; // topbar and paddings
    }
    this.width = this.get_width();
    this.height = this.get_height();
}

$(document).ready(function () {

    /*
     * Global variables. They are available without the window namespace, too.
     */
    window.player1     = new Player();
    window.yourlib     = new Yourlib();
    window.collection  = new Collection();
    window.browse      = new Browse();
    window.playlist    = new Playlist();
    window.upload      = new Upload();
    window.download    = new Download();
    window.sidebar     = new Sidebar(); // must be last?
    window.context_content = new ContextContent();

    context_content.update_viewport(); // must be first
    browse.bind();
    collection.bind();
    playlist.bind();
    sidebar.bind();

    /*
     * Event delegation. They will work globally on dynamic content, too.
     * Events and functionality that cannot be bind like that, must be bound
     * manually with <object>.bind(), e.g. sidebar.bind()
     */

    /* update viewport */
    $(window).resize(function() {
        browse.update_viewport();
      context_content.update_viewport();
      collection.update_viewport();
      playlist.update_viewport();
    });
    /* global header */
    $(document).on("click",  "#logout",                   yourlib.logout);
    $(document).on("click",  "#btn_rescan_library",       yourlib.rescan);

    /* player */
    $(document).on("click",  "#btn_player1_next",         player1.next);

    /* sidebar */
    $(document).on("click",  "#btn_context_collection",   sidebar.show_collection);
    $(document).on("click",  "#btn_sidebar_browse",       sidebar.show_browse);
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
    $(document).on("click",   "#btn_collection_toggle_filter", collection.toggle_filter);
    $(document).on("submit",  "#context_collection_search", collection.search);
    $(document).on("click",   "#get_more_results",          collection.get_more_results);
    $(document).on("appear",  "#get_more_results",          collection.get_more_results, {one: false});
    $(document).on("click",   ".btn_filter_genre",          collection.filter_genre);

    /* browse */
    $(document).on("click",   ".btn_browse_artist",         browse.on_artist_clicked);

    /* collection & playlist */
    $(document).on("click",      ".song_item",  collection.song_play);
    $(document).on("mouseenter", ".song_item", function(){$(this).removeClass("ui-state-default").addClass("ui-state-focus")});
    $(document).on("mouseleave", ".song_item", function(){$(this).removeClass("ui-state-focus").addClass("ui-state-default")});

    /* some global ui theming */
    $(".btn").on("mouseenter", function(){$(this).removeClass("ui-state-default").addClass("ui-state-focus")});
    $(".btn").on("mouseleave", function(){$(this).removeClass("ui-state-focus").addClass("ui-state-default")});

    /* check document state, maybe there are ongoing actions in progress */
    if ( $( "#rescan_status" ).html() != "" ) {
        yourlib.check_scan_status();
    }

    /* add csrf cookie to every POST */
    $(document).ajaxSend(function(event, xhr, settings) {
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

});

