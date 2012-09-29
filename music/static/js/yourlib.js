/* yourlib common stuff, find context specific stuff in subsequent yourlib_<files>.js  */

function spinner_start(elem) {
    $(elem).append("<img class='spinner'  height='15' width='15' src='/static/css/spinner.gif' />");
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

function Pagination(options) {
    console.log("PAGINATION INITIALIZED");

    // this is somehow useless
    this.scrollTarget = options.scrollTarget;  // the dom which listen to scroll events
    this.appendTarget = options.appendTarget;  // the dom where to append data to
    this.contentUrl   = options.contentUrl;    // where to load data from
    this.contentData  = options.contentData;   // data to send to server within load request
    this.beforeLoad   = options.beforeLoad;    // execute this before load
    this.afterLoad    = options.afterLoad;     // exectute after succesful load
    this.errorLoad    = options.errorLoad;     // execute this on load errors
    this.enabled      = options.enabled;       // doh.

    // extend options
    options.loadContent     = this.loadContent;
    options.contentReceived = this.contentReceived;
    //options.loadError       = this.loadError;

    // save options into dom element
    $(this.scrollTarget).data("pagination", options);

    // bind scroll event
    $(this.scrollTarget).scroll(function(event){
        // context: window. `this` is window, `$(this)` is dom element that was scrolled (scrollTarget)
        // I hate javascript.
        var pagination = $(this).data("pagination"); // get pagination object
        console.log("PAGINATION SCROLL EVENT");
        if (pagination.enabled) {
            console.log("PAGINATION SCROLL ALLOWED");
            // determine scroll position
            var scrolled           = $(pagination.scrollTarget).scrollTop();
            var scrollTargetHeight = $(pagination.scrollTarget).height();
            var appendTargetHeight = $(pagination.appendTarget).height();
            var mayLoadContent = scrolled + scrollTargetHeight + 10 >= appendTargetHeight;

            if (mayLoadContent) {
                pagination.beforeLoad();
                $(pagination.appendTarget).children().attr("rel", "loaded"); // mark already loaded data
                pagination.loadContent(pagination);
            }
        }
    });

    this.loadContent = function(pagination) {
        // I really don't know the context of this or $(this) here.
        $this = $(pagination.scrollTarget);

        $.ajax({
            type:     "POST",
            url:      pagination.contentUrl,
            data:     {"so_far" : pagination.contentData},
            success:  function(data) {
                // we are in context window again. sigh.
                pagination = $($this).data("pagination");
                console.log("PAGINATION LOAD SUCCESS");
                if (data == "nomoreresults") {
                    pagination.enabled = false;
                }
                else {
                    $(pagination.appendTarget).append(data);
                    var newData = $(pagination.appendTarget).children("[rel!=loaded]");
                    pagination.afterLoad(newData);
                }
            },
            error:    function(data) {
                // we are in context window again. sigh.
                pagination = $($this).data("pagination");

                console.log("PAGINATION LOAD ERROR");
                pagination.errorLoad(data);
            },
            datatype: "html"
        })
    }
}

function Browse() {

    this.bind = function(selector) {

/*   $(function(){
        $('#context_browse_artist_container').scrollPagination({
            'contentPage': 'collection/browse/more/artist/', // the url you are fetching the results
            'contentData': {"so_far": function() {return $(".btn_browse_artist").length;}}, // these are the variables you can pass to the request, for example: children().size() to know which page you are
            'scrollTarget': $("#context_browse_artist_container"), // who gonna scroll? in this example, the full window
            'appendTarget': $("#context_browse_artist_column"),  // where to append loaded data
            'heightOffset': 10, // it gonna request when scroll is 10 pixels before the page ends
            'beforeLoad': function(){ // before load function, you can display a preloader div
                $('#loading_browse_artists').fadeIn();
            },
            'afterLoad': function(elementsLoaded){ // after loading content, you can use this function to animate your new elements
                 $('#loading_browse_artist').fadeOut();
                 //var i = 0;
                 //$(elementsLoaded).fadeInWithDelay();
                 //if ($('#song_items').children().size() > 100){ // if more than 100 results already loaded, then stop pagination (only for testing)
                 //   $('#nomoreresults').fadeIn();
                 //   $('#song_items').stopScrollPagination();
                 //}
                 browse.update_viewport();
            }
        });

        // code for fade in element by element
        $.fn.fadeInWithDelay = function(){
            var delay = 0;
            return this.each(function(){
                $(this).delay(delay).animate({opacity:1}, 200);
                delay += 100;
            });
        };
    });


   $(function(){
        $('#context_browse_title_container').scrollPagination({
            'contentPage': 'collection/browse/more/title/', // the url you are fetching the results
            'contentData': {"so_far": function() {return $(".btn_browse_title").length;}}, // these are the variables you can pass to the request, for example: children().size() to know which page you are
            'scrollTarget': $("#context_browse_title_container"), // who gonna scroll? in this example, the full window
            'appendTarget': $("#context_browse_title_column"),  // where to append loaded data
            'heightOffset': 10, // it gonna request when scroll is 10 pixels before the page ends
            'beforeLoad': function(){ // before load function, you can display a preloader div
                $('#loading_browse_title').fadeIn();
            },
            'afterLoad': function(elementsLoaded){ // after loading content, you can use this function to animate your new elements
                 $('#loading_browse_title').fadeOut();
                 //var i = 0;
                 //$(elementsLoaded).fadeInWithDelay();
                 //if ($('#song_items').children().size() > 100){ // if more than 100 results already loaded, then stop pagination (only for testing)
                 //   $('#nomoreresults').fadeIn();
                 //   $('#song_items').stopScrollPagination();
                 //}
                 browse.update_viewport();
            }
        });

        // code for fade in element by element
        $.fn.fadeInWithDelay = function(){
            var delay = 0;
            return this.each(function(){
                $(this).delay(delay).animate({opacity:1}, 200);
                delay += 100;
            });
        };
    });



   $(function(){
        $('#context_browse_album_container').scrollPagination({
            'contentPage': 'collection/browse/more/album/', // the url you are fetching the results
            'contentData': {"so_far": function() {return $(".btn_browse_album").length;}}, // these are the variables you can pass to the request, for example: children().size() to know which page you are
            'scrollTarget': $("#context_browse_album_container"), // who gonna scroll? in this example, the full window
            'appendTarget': $("#context_browse_album_column"),  // where to append loaded data
            'heightOffset': 10, // it gonna request when scroll is 10 pixels before the page ends
            'beforeLoad': function(){ // before load function, you can display a preloader div
                $('#loading_browse_album').fadeIn();
            },
            'afterLoad': function(elementsLoaded){ // after loading content, you can use this function to animate your new elements
                 $('#loading_browse_album').fadeOut();
                 //var i = 0;
                 //$(elementsLoaded).fadeInWithDelay();
                 //if ($('#song_items').children().size() > 100){ // if more than 100 results already loaded, then stop pagination (only for testing)
                 //   $('#nomoreresults').fadeIn();
                 //   $('#song_items').stopScrollPagination();
                 //}
                 browse.update_viewport();
            }
        });

        // code for fade in element by element
        $.fn.fadeInWithDelay = function(){
            var delay = 0;
            return this.each(function(){
                $(this).delay(delay).animate({opacity:1}, 200);
                delay += 100;
            });
        };
    });
*/
        console.log("binding browse view. selector: " + selector);

        artistPagination = Pagination({
            scrollTarget : '#context_browse_artist_container',
            appendTarget : "#context_browse_artist_column",
            contentUrl   : "collection/browse/more/artist/",
            contentData  : function() {return $(".btn_browse_artist").length;},
            beforeLoad   : function() {$('#loading_browse_artists').fadeIn();},
            afterLoad    : function() {$('#loading_browse_artists').fadeOut();},
            errorLoad    : function() {alert("Pagination load error");},
            enabled      : true
        });

        albumPagination = Pagination({
            scrollTarget : '#context_browse_album_container',
            appendTarget : "#context_browse_album_column",
            contentUrl   : "collection/browse/more/album/",
            contentData  : function() {return $(".btn_browse_album").length;},
            beforeLoad   : function() {$('#loading_browse_album').fadeIn();},
            afterLoad    : function() {$('#loading_browse_album').fadeOut();},
            errorLoad    : function() {alert("Pagination load error");},
            enabled      : true
        });

        titlePagination = Pagination({
            scrollTarget : '#context_browse_title_container',
            appendTarget : "#context_browse_title_column",
            contentUrl   : "collection/browse/more/title/",
            contentData  : function() {return $(".btn_browse_title").length;},
            beforeLoad   : function() {$('#loading_browse_title').fadeIn();},
            afterLoad    : function() {$('#loading_browse_title').fadeOut();},
            errorLoad    : function() {alert("Pagination load error");},
            enabled      : true
        });

/*
        $('#context_browse_artist_container').data("enabled", true);
        $('#context_browse_artist_container').data("contentUrl", "collection/browse/more/artist/");
        $('#context_browse_artist_container').data("appendTarget", "#context_browse_artist_column");
        $('#context_browse_artist_container').data("contentData", function() {
            return $(".btn_browse_artist").length;
        });
        $('#context_browse_artist_container').data("beforeLoad", function() {
            $('#loading_browse_artists').fadeIn();
        });
        $('#context_browse_artist_container').data("afterLoad", function() {
            $('#loading_browse_artists').fadeOut();
        });
        $('#context_browse_artist_container').scroll(function() {
            var $appendTarget = $("#context_browse_artist_column");
            var mayLoadContent = $(this).scrollTop() + $(this).height() + 10 >= $appendTarget.height();
            if (mayLoadContent) {
                $(this).data("beforeLoad"); // execute beforeLoad function
                $(this).children().attr("rel", "loaded"); // mark already loaded data
                $this = $(this); // make current element available in ajax success function
                browse.pagination($this);
            }
        });
*/
        this.update_viewport();

        if (!selector) {
            selector = '';
            // all columns
            column_selector = "#browse_artist_filter .btn, #browse_album_filter .btn, #browse_genre_filter .btn";
        }
        else {
            // one column max.
            column_selector = selector + " .btn";
        }

        $( selector + " .btn_browse_title").on("click", function(){
            var $data = {
                'song_id': $(this).attr("data-title_id"),
                'source' : 'collection',
            };
            $.post("play/", $data, function(song_info) {
                player1.play_song(song_info);
            });
            return false;
        });

        $( column_selector ).on("mouseenter", function(){$(this).removeClass("ui-state-default").addClass("ui-state-focus")});
        $( column_selector ).on("mouseleave", function(){$(this).removeClass("ui-state-focus").addClass("ui-state-default")});

        // select/deselect items
        $( column_selector ).not( ".btn_browse_title" )
        /*.on("mouseenter", function() {
            $this = $(this);
            if ($this.hasClass("pre-selected") || $this.hasClass("pre-unselected")) {
                return;
            }
            if ($this.hasClass("selected")) {
                $this.addClass("pre-unselected");
                //$this.data('delay', setTimeout(function() {$this.removeClass("selected"); browse.on_artist_clicked()}, 900));
                $this.data('delay', setTimeout(function() {

                    var column = $this.parent().find(".ui-widget-header").html();

                    $this.removeClass("selected");
                    browse.on_column_item_clicked(column);
                }, 1500));
            }
            else {
                $this.addClass("pre-selected");
                //$this.data('delay', setTimeout(function() {$this.removeClass("pre-selected").addClass("selected"); browse.on_artist_clicked()}, 900));
                $this.data('delay', setTimeout(function() {

                    var column = $this.parent().find(".ui-widget-header").html();

                    $this.removeClass("pre-selected").addClass("selected");
                    browse.on_column_item_clicked(column);
                }, 1500));
            }
        })
        .on("mouseleave", function() {
            $this = $(this);
            if ($this.hasClass("pre-selected") || $this.hasClass("pre-unselected")) {
                clearTimeout($this.data("delay"));
                $this.removeClass("pre-selected");
                $this.removeClass("pre-unselected");
            }
        })*/
        .on("click", function() {
            console.log("column item clicked");

            var column = $(this).parent().find(".ui-widget-header").html();

            // highlight/unhighlight
            if ($(this).hasClass("selected")) {
                $(this).removeClass("selected")
            }
            else{
                $(this).addClass("selected")
            }

            // prevent ongoing timeouts
            if ($(this).hasClass("pre-selected") || $(this).hasClass("pre-unselected")) {
                clearTimeout($(this).data("delay"));
                $(this).removeClass("pre-selected");
                $(this).removeClass("pre-unselected");
            }

            browse.on_column_item_clicked(column);

        })
        .draggable({
            items: "li",
            helper: function(event) {
                var column = $(this).parent().find(".ui-widget-header").html();

                helper = $("<div class='ui-widget-content ui-state-focus ui-corner-all', align='center'></div>");
                helper.attr("data-source", "browse");
                helper.attr("data-column", column);

                if ("artist" == column) {
                    artist = $(this).find(".name").html();
                    artist_id = $(this).attr("data-artist_id");
                    helper.attr("data-artist_id", artist_id);
                    count = $(this).find(".count").html();
                    //title = $(this).find(".title").html();
                    console.log("Dragging element with song id TODO")
                    helper.html("All songs (" + count + ") from artist <br />" + artist);
                    return $( helper );
                }
                else if ("album" == column) {

                }
                else if ("genre" == column) {

                }


            },
            appendTo: "body",
            containment: "document",
            revert: "invalid",
            delay: 100,
        }).disableSelection();
    }
    
    this.pagination = function(loadElement) {
        $this = loadElement;
        beforeLoad = $this.data("beforeLoad");
        beforeLoad();
        if ($this.data("enabled")) {
            $.ajax({
                type: "POST",
                url: $this.data("contentUrl"),
                data: {"so_far": $($this).data("contentData")()},
                success: function(data) {
                    if (data == "nomoreresults") {
                        $this.data("enabled", false);
                    }
                    else {
                        $($this.data("appendTarget")).append(data);
                        var newData = $($this.data("appendTarget")).children("[rel!=loaded]");
                        afterLoad = $this.data("afterLoad");
                        afterLoad(newData);
                    }
                },
                dataType: "html"
            });
        }
        else {
            afterLoad = $($this).data("afterLoad");
            afterLoad();
        }
    }

    this.on_column_received = function(data) {
        var $album_container  = $(data).find("#context_browse_album_container");
        var $genre_container  = $(data).find("#context_browse_genre_container");
        var $title_container  = $(data).find("#context_browse_title_container");
        var $artist_container = $(data).find("#context_browse_artist_container");

        var column_from = $(data).find("#column_from").html();

        if ($album_container.length > 0) {
            if ($("#context_container").find("#context_browse_album_container").length > 0) {
                $("#context_browse_album_container").replaceWith($album_container);
                browse.bind("#context_browse_album_container");
            }
        }

        if ($title_container.length > 0) {
            if ($("#context_container").find("#context_browse_title_container").length > 0) {
                $("#context_browse_title_container").replaceWith($title_container);
                browse.bind("#context_browse_title_container");
            }
        }

        if ($genre_container.length > 0) {
            console.log("TODO");
        }
        if ($artist_container.length > 0) {
            console.log("TODO");
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

