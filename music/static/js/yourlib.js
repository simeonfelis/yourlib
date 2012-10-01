/* yourlib common stuff, find context specific stuff in subsequent yourlib_<files>.js  */

function spinner_start(elem) {
    $(elem).append("<img class='spinner'  height='15' width='15' src='/static/css/spinner.gif' />");
}

function spinner_stop(sel) {
    $( sel ).find( ".spinner" ).fadeOut(500);
}

function highlight_playing(by_who, target) {

    if (by_who) {
        console.log("highlight_playling by", by_who, " for ", target);
    }
    else {
        console.log("highlight_playling by unknown");
    }

    var playlist_id = $( "#player1" ).attr("data-playlist_id");
    var item_id     = $( "#player1" ).attr("data-item_id");
    var song_id     = $( "#player1" ).attr("data-song_id");
    var source      = $( "#player1" ).attr("data-source");

    $( target + " .currently_playing" ).find(".playing_icon").remove();
    $( target + " .currently_playing" ).removeClass("currently_playing").removeClass("ui-state-active");

    if ("playlist" == source) {
        sidebar_sel = "#sidebar_playlist_" + playlist_id;
        context_sel = "#playlist_" + playlist_id + "_item_" + item_id;
    }
    else if ("browse" == source) {
        sidebar_sel = "#btn_sidebar_browse";
        context_sel = "[data-title_id=" + song_id + "]";
    }
    else if ("collection" == source) {
        sidebar_sel = "#btn_context_collection";
        context_sel = "#collection_song_id_" + song_id;
    }
    else {
        console.log("Cannot highlight: unknow source");
        return;
    }

    $(target + " " + sidebar_sel)
        .addClass("currently_playing")
        .append("<span class='playing_icon'>♬</span>");

    $(target + " " + context_sel).addClass("currently_playing").addClass("ui-state-active");

    /* sidebar */
   /*
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
*/
    /* context content. sel was created either for playlist or collection */
  //  if ( $( sel ).hasClass("currently_playing") ) {
        // don't re-apply
 //   }
  //  else {
        //$( "#context_content" ).find( ".currently_playing" ).find(".playing_icon");
        //$( "#context_content" ).find( ".currently_playing" ).addClass("ui-state-default");
        //$( "#context_content" ).find( ".currently_playing" ).removeClass("currently_playing");
        //$( sel ).removeClass("ui-state-default");
        //$( sel ).addClass("currently_playing");
        //$( sel ).addClass("ui-state-highlight");
    //}
}


function Download() {
    this.bind = function() {
    }
}

function Pagination(options) {
    //console.log("PAGINATION INITIALIZED");

    // this is somehow useless
    this.scrollTarget = options.scrollTarget;  // the dom which listen to scroll events
    this.appendTarget = options.appendTarget;  // the dom where to append data to
    this.contentUrl   = options.contentUrl;    // where to load data from
    this.contentData  = options.contentData;   // data to send to server within load request
    this.beforeLoad   = options.beforeLoad;    // execute this before load
    this.afterLoad    = options.afterLoad;     // exectute after succesful load
    this.errorLoad    = options.errorLoad;     // execute this on load errors
    this.enabled      = options.enabled;       // doh.

    // some functions have to be defined on top
    this.loadContent = function(paginator) {
        var tmp = this;
        // I really don't know the context of this or $(this) here.
        // So I need to know what context I am. paginator has to be a
        // Pagination() object.
        $this = $(paginator.scrollTarget);

        console.log("PAGINATOR LOAD: SO_FAR:" + paginator.contentData())

        $(paginator.appendTarget).children().attr('rel', 'loaded');

        $.ajax({
            type:     "POST",
            url:      paginator.contentUrl,
            data:     {"so_far" : paginator.contentData},
            success:  function(data) {
                // we are in context window again. sigh.
                paginator = $($this).data("pagination");
                if (data == "nomoreresults") {
                    paginator.enabled = false;
                }
                else {
                    $(paginator.appendTarget).append(data);
                    var newData = $(paginator.appendTarget).children("[rel!=loaded]");
                }
                paginator.afterLoad(newData);
                paginator.loading = false;
                $($this).data("pagination", paginator);
            },
            error:    function(data) {
                // we are in context window again. sigh.
                paginator = $($this).data("pagination");

                //console.log("PAGINATION LOAD ERROR");
                paginator.errorLoad(data);
                paginator.loading = false;
                $($this).data("pagination", paginator);
            },
            datatype: "html"
        })
    }

    // extend options
    options.loadContent     = this.loadContent;
    options.loading         = false;

    // save options into dom element
    $(this.scrollTarget).data("pagination", options);

    // bind scroll event
    $(this.scrollTarget).scroll(function(event){
        //console.log("PAGINATION SCROLL EVENT");
        // context: window. `this` is window, `$(this)` is dom element that was scrolled (scrollTarget)
        // I hate javascript.
        var pagination = $(this).data("pagination"); // get pagination object
        if (pagination.enabled && !pagination.loading) {
            // determine scroll position
            var scrolled           = $(pagination.scrollTarget).scrollTop();
            var scrollTargetHeight = $(pagination.scrollTarget).height();
            var appendTargetHeight = $(pagination.appendTarget).height();
            var mayLoadContent = scrolled + scrollTargetHeight + 50 >= appendTargetHeight;

            if (mayLoadContent) {
                pagination.loading = true;               // block further loading until this one is done
                $(this).data("pagination", pagination);
                pagination.beforeLoad();
                $(pagination.appendTarget).children().attr("rel", "loaded"); // mark already loaded data
                pagination.loadContent(pagination);
            }
        }
        else if (pagination.loading) {
            console.log("PAGINATION BLOCK BECAUSE OF ONGOING LOAD (scrolling to fast?)");
        }
    });
}

function ContextContent() {
    this.update_viewport = function() {
        this.width = this.get_width();
        this.height = this.get_height();
        $("#context_container").height(this.height);
        $("#context_container").width(this.width);
    }
    this.get_width = function() {
        return $(window).width() - 300 - 20; // sidebar and paddings
    }
    this.get_height = function() {
        return $(window).height() - 50 - 20; // topbar and paddings
    }
    this.width = this.get_width();
    this.height = this.get_height();
}

function yourlib_resize_cb() {

      context_content.update_viewport();

      browse.update_viewport();
      collection.update_viewport();
      playlist.update_viewport();
      upload.update_viewport();
}

$(document).ready(function () {

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

    // update viewport
    var resizeTimer = 0;
    $(window).resize(function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(yourlib_resize_cb, 100);
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
    $(document).on("click",  "#btn_sidebar_upload",       sidebar.show_upload);
    //$(document).on("click",  "#btn_context_download",     sidebar.show_download);
    $(document).on("submit", "#playlist_create",          playlist.create);

    /* playlist */
    $(document).on("click",  ".btn_playlist_item_play",   playlist.item_play);
    $(document).on("click",  ".btn_playlist_item_remove", playlist.item_remove);
    $(document).on("click",  ".btn_playlist_delete",      playlist.delete_list);
    $(document).on("click",  ".btn_playlist_download",    playlist.download);

    /* collection */
    //$(document).on("click",   "#btn_collection_toggle_filter", collection.toggle_filter);
    $(document).on("submit",  "#context_collection_search", collection.search);
    //$(document).on("click",   "#get_more_results",          collection.get_more_results);
    //$(document).on("appear",  "#get_more_results",          collection.get_more_results, {one: false});
    //$(document).on("click",   ".btn_filter_genre",          collection.filter_genre);

    /* browse */
    //$(document).on("click",   ".btn_browse_artist",         browse.on_artist_clicked);

    /* collection & playlist */
    //$(document).on("click",      ".song_item",  collection.song_play);
    $(document).on("mouseenter", ".song_item", function(){$(this).addClass("ui-state-hover")});
    $(document).on("mouseleave", ".song_item", function(){$(this).removeClass("ui-state-hover")});

    /* some global ui theming */
    $(".btn").on("mouseenter", function(){$(this).addClass("ui-state-hover")});
    $(".btn").on("mouseleave", function(){$(this).removeClass("ui-state-hover")});

    /* check document state, maybe there are ongoing actions in progress */
    if ( $( "#rescan_status" ).html() != "" ) {
        yourlib.check_scan_status();
    }

});

