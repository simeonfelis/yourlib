function Playlist() {

    // init (constructor) at end of function

    this.highlight = function() {
        $(this).addClass("ui-state-hover");
    }
    this.unlight = function() {
        $(this).removeClass("ui-state-hover");
    }

    this.bind = function () {

        console.log("============ Playlist bind =============");

        // make sure to bind only once
        $("#context_playlist_container .song_item").off("mouseenter", this.highlight);
        $("#context_playlist_container .song_item").off("mouseleave", this.unlight);

        $("#context_playlist_container .song_item").on("mouseenter", this.highlight);
        $("#context_playlist_container .song_item").on("mouseleave", this.unlight);

        $("#context_playlist_container .btn_playlist_item_remove").on("click", this.remove_item);

        var is_shared = false;
        if ($("#shared_playlist").length > 0) {
            is_shared = true;
        }

        if (!is_shared) {
            // TODO: btn delete

            // btn share
            $(".btn_playlist_share").on("click", this.share);

            // Dragndrop sorting
            $("#context_playlist_container .sortable").sortable( {
                items: "li:not(.song_item_heading):not(.song_info)",
                start: function(event, ui) {
                    $(ui.helper).addClass("ui-state-active");
                },
                stop: this.reorder,
                //activeClass: "ui-state-active",
                delay: 100,
            });
        }
        $(".sortable").disableSelection();
    }

    this.username_validation = function() {
        console.log("username validation started");
        var username = $("#dialog-playlist-share-username").val();

        var data = {
            'username'            : username,
        };

        var url = base_url + "username_validation/";

        $.ajax({
            type:     "GET",
            url:      url,
            data:     data,
            success:  function(data, status, jqXHR) {
                // we are in context window again. sigh.

                // get DOM object of Share btn in dialog. Sorry for this mess.
                var $dia = $("#dialog-playlist-share").parent();
                var $tmp = $dia.find("button span:contains('Share')");
                var $share_btn = $tmp.parent();

                var exists = $.parseJSON( data );

                if (exists["exists"] == true) {
                    $share_btn.show();
                }
                else {
                    $share_btn.hide();
                }
            },
            error:    function(jqXHR, status, error) {
                // we are in context window again. sigh.
                console.log("ERROR VALIDATING USERNAME");
                $share_btn.hide();
            },
            complete:    function(jqXHR, textStatus) {
            },
            datatype: "json"
        });

    }
    this.share = function(event, ui, playlist_id, username) {
        if (playlist_id) {

                var data = {
                    'username'            : username,
                };

                var url = "share/";

                $.ajax({
                    type:     "POST",
                    url:      url,
                    data:     data,
                    success:  function(data, status, jqXHR) {
                        // we are in context window again. sigh.
                        console.log("Sharing succes?");

                    },
                    error:    function(jqXHR, status, error) {
                        // we are in context window again. sigh.
                        console.log("SHARE PLAYLIST ERROR");
                    },
                    complete:    function(jqXHR, textStatus) {
                    },
                    datatype: "html"
                });

                return false; // Don't do anything else
        }
        else {
            // bind dialog events
            $("#dialog-playlist-share-username").off("keyup", this.username_validation);
            $("#dialog-playlist-share-username").on("keyup", playlist.username_validation);

            // show dialog
            $this = $(this);
            playlist_id = $(this).attr("data-playlist_id");
            //playlist_id = $( "#dialog-playlist-share" ).find(".playlist_name").html($(this).attr("data-playlist_name"));
            $( "#dialog-playlist-share" ).dialog({
                resizable: true,
                height:400,
                width:500,
                modal: true,
                buttons: {
                    "Cancel": function(event) {
                        $( this ).dialog( "close" );
                    },
                    "Share": function(event) {
                        username = $("#dialog-playlist-share-username").val();
                        $( this ).dialog( "close" );
                        playlist.share(null, null, playlist_id, username);
                    }
                }
            });
            // TODO: hide share button on default
            $share_btn = $("#dialog-playlist-share button span:contains('Share')");
            $share_btn.hide();
        }
    }

    this.reorder = function (event, ui) {
        /* callback when dragndrop stoped */
        /* when an element was reordered, this is called */

        var playlist_id = $(ui.item).attr("data-playlist_id");
        var item_id     = $(ui.item).attr("data-item_id");

        var $prev = $(ui.item).prev();
        var prev_item_id = $prev.attr("data-item_id");

        if (typeof prev_item_id == "undefined") {
            prev_item_id = 0;
        }

        var data = {
            'item_id'            : item_id,
            'item_previous_id'   : prev_item_id,
        };

        var url = "reorder/";

        $(".overlay").show();

        $.ajax({
            type:     "POST",
            url:      url,
            data:     data,
            success:  function(data, status, jqXHR) {
                // we are in context window again. sigh.

                playlist.new_context = $(data).find("#context_playlist");

                //$("#context_playlist").fadeOut("fast", function() {
                    $("#context_playlist").replaceWith(playlist.new_context).fadeIn("fast");
                    playlist.bind();
                    playlist.update_viewport();
                //});

            },
            error:    function(jqXHR, status, error) {
                // we are in context window again. sigh.
                console.log("PLAYLIST ITEM REMOVED ERROR");
                //$( "#player1_song_info_artist" ).html(status + ": " + error);
            },
            complete:    function(jqXHR, textStatus) {
                $(".overlay").hide();
            },
            datatype: "html"
        });

        return false; // Don't do anything else
        // update playlist content. TODO: should be done with only one request!
        //$( "#context_playlist_container" ).load("reorder/", data, function() {
        //    highlight_playing("playlist.reorder()", "#context_playlist");
        //    playlist.bind();
        //})
        //.error(function() {alert("error ordering playlist item");});
    }

    this.item_play = function () {
        /* will be called on clicks on items play btn in playlist */
        var data = {
            'song_id'            : $(this).attr("data-song_id"),
            'playlist_id'        : $(this).attr("data-playlist_id"),
            'item_id'            : $(this).attr("data-item_id"),
            'source'             : 'playlist',
        };

       var url = "play/";

        $.ajax({
            type:     "POST",
            url:      url,
            data:     data,
            success:  function(data, status, jqXHR) {
                // we are in context window again. sigh.
                song_info = data;
                player1.play_song(song_info);
            },
            error:    function(jqXHR, status, error) {
                // we are in context window again. sigh.
                $( "#player1_song_info_artist" ).html(status + ": " + error);
            },
            complete: function(jqXHR, textStatus) {
            },
            datatype: "html"
        });

        return false; // Don't do anything else
    }

    this.remove_item = function() {
        //var playlist_id = $(this).closest(".song_item").attr("data-playlist_id");
        var item_id     = $(this).closest(".song_item").attr("data-item_id");

        data = {
            "item_id": item_id,
        }

        var url = "remove_item/";

        $(".overlay").show();

        $.ajax({
            type:     "POST",
            url:      url,
            data:     data,
            success:  function(data, status, jqXHR) {
                // we are in context window again. sigh.

                playlist.new_context = $(data).find("#context_playlist");

                //$("#context_playlist").fadeOut("fast", function() {
                    $("#context_playlist").replaceWith(playlist.new_context).fadeIn("fast");
                    playlist.bind();
                    playlist.update_viewport();
                //});

                sidebar_data = $(data).find("#sidebar_playlists_content");
                $("#sidebar_playlists_content").replaceWith(sidebar_data);
                sidebar.bind_playlist_items();
                sidebar.update_viewport();

            },
            error:    function(jqXHR, status, error) {
                // we are in context window again. sigh.
                console.log("PLAYLIST ITEM REMOVED ERROR");
            },
            complete: function(jqXHR, textStatus) {
                $(".overlay").hide();
            },
            datatype: "html"
        });

        return false; // Don't do anything else
    }

    this.delete_list = function($playlist, confirmed) {
        /* will be called on clicks on delete btn of a playlist */

        if (confirmed === true) {
            var playlist_id = $playlist.attr("data-playlist_id")
            var data = {};

            var url = "delete/";

            $.ajax({
                type:     "POST",
                url:      url,
                data:     data,
                success:  function(data, status, jqXHR) {
                    // we are in context window again. sigh.

                    playlist.new_context = $(data).find("#context_playlist");

                    $("#context_playlist").fadeOut("fast", function() {
                        $("#context_playlist").replaceWith(playlist.new_context).fadeIn("fast");
                        playlist.bind();
                        playlist.update_viewport();

                        playlist_id = $(playlist.new_context).attr("data-playlist_id");
                        var stateObj = null; var title = "";
                        var url = base_url + "playlist/" + playlist_id + "/";
                        history.pushState(stateObj, title, url);

                    });

                    sidebar_data = $(data).find("#sidebar_playlists_content");
                    $("#sidebar_playlists_content").replaceWith(sidebar_data);
                    sidebar.bind_playlist_items();
                    sidebar.update_viewport();

                },
                error:    function(jqXHR, status, error) {
                    // we are in context window again. sigh.
                    console.log("PLAYLIST DELETED ERROR");
                },
                complete: function(jqXHR, textStatus) {
                    $(".overlay").hide();
                },
                datatype: "html"
            });

            return false; // Don't do anything else


            /* get new view for context */
            $( "#context_content" ).load(base_url + "playlist/" + playlist_id + "/delete/", $data, function() {

                /* update playlists in sidebar */
                $( "#sidebar_playlists_content" ).load("sidebar/playlists/", function() {
                    highlight_playing("playlist.delete_list()", "#context_playlist");
                    sidebar.bind("#sidebar_playlists_content");
                });

                playlist.bind();

            });
        }
        else {
            $this = $(this);
            $( "#dialog-confirm-playlist-delete" ).find(".playlist_name").html($(this).attr("data-playlist_name"));
            $( "#dialog-confirm-playlist-delete" ).dialog({
                resizable: true,
                height:300,
                width:400,
                modal: true,
                buttons: {
                    "Keep playlist": function() {
                        $( this ).dialog( "close" );
                    },
                    "Delete playlist": function() {

                        playlist.delete_list($playlist=$this, confirmed=true);

                        $( this ).dialog( "close" );
                    }
                }
            });

        }

        return false; // Don't do anything else
    }
    this.download = function() {
        var $data = {
            'csrfmiddlewaretoken' : csrf_token,
            'playlist_id'         : $(this).attr("data-playlist_id"),
        };
        $.post("playlist/download/", $data, function(msg) {
            alert(msg);
        });
    }

    this.append = function(playlist_id, item_id, source) {
        var data = {
            "item_id" :          item_id,
            "source" :      source,
        };

       var url = base_url + "playlist/" + playlist_id + "/append/";

        $.ajax({
            type:     "POST",
            url:      url,
            data:     data,
            success:  function(data, status, jqXHR) {
                console.log("playlist item appended");
                // we are in context window again. sigh.
                var selector = "#sidebar [data-playlist_id=" + data["playlist_id"] + "] .count";
                var $sidebar_playlist_count = $(selector);
                $sidebar_playlist_count.html(data["count"]);
            },
            error:    function(jqXHR, status, error) {
                console.log("playlist item append error");
                // we are in context window again. sigh.
            },
            datatype: "json"
        });

        return false; // Don't do anything else
    }
    this.create = function(event) {
        /* will be called on submit of create playlist field forms */
        event.preventDefault();

        var name = $.trim( $( "#playlist_create_name" ).val() );

        if ( !(name.length > 0) ) {
            console.log("Empty name for playlist");
            return false;
        }

        var data = {
            'playlist_name': name,
        };

        var url = $(this).attr("action");

        $.ajax({
            type:     "POST",
            url:      url,
            data:     data,
            success:  function(data, status, jqXHR) {
                // we are in context window again. sigh.

                newData = $(data).find("#sidebar_playlists_content");
                $("#sidebar_playlists_content").replaceWith(newData);
                sidebar.bind_playlist_items();
                sidebar.update_viewport();

            },
            error:    function(jqXHR, status, error) {
                // we are in context window again. sigh.
                console.log("ERROR CREATING PLAYLIST");
            },
            complete:    function(jqXHR, textStatus) {
            },
            datatype: "html"
        });

/*        $( "#sidebar_playlists_content" ).load("playlist/create/", $data, function() {
            $( "#playlist_create_name" ).val("");
            sidebar.bind();
        })
        .error(function() {alert("Error creating playlist");});
        */

        return false; // Don't do anything else
    }

    this.exhibit = function(playlist_id, url, exhibit_finished_cb) {
        console.log("PLAYLIST EXHIBIT CALLED FOR PL " + playlist_id);

        this.exhibit_finished = exhibit_finished_cb;
            var data = {};

            this.active_id = playlist_id;

            $.ajax({
                type:     "GET",
                url:      url,
                data:     data,
                success:  function(data, status, jqXHR) {
                    // we are in context window again. sigh.

                    // store fetched data
                    playlist.view = $(data).find("#context_playlist");

                    // highlight current in sidebar
                    $("#sidebar").find(".currently_shown").removeClass("currently_shown");
                    $(playlist.active_sidebar).addClass("currently_shown");

                    // fade out whatever is just viewed
                    $("#context_content").children().fadeOut("slow");
                    // as there is usually more than one child in context_content,
                    // wait until all fadeOuts are finished 
                    $("#context_content").children().promise().done(function() {

                        // remove eventually displayed playlist
                        $("#context_playlist").remove();

                        // insert
                        $("#context_content").append($(playlist.view).fadeIn("slow", function() {
                            // the exhibit process is finished here
                            playlist.exhibit_finished();

                        }));
                        // new playlist is now in DOM. update layout before fadeIn is finished
                        playlist.update_viewport();
                        highlight_playing("playlist.exhibit()", "#context_playlist");
                        playlist.bind();
                    })
                },
                error:    function(jqXHR, status, error) {
                    // we are in context window again. sigh.
                    console.log("ERROR SHOWING PLAYLIST");
                },
                complete:    function(jqXHR, textStatus) {
                },
                datatype: "html"
            });
    }

    this.update_viewport = function() {

        console.log("============ Playlist update_viewport =============");


        if ($.find("#context_playlist_container").length == 0) {
            // nothing to update
            return;
        }
        var height = context_content.height - $("#context_header").height() - 1;
        $("#context_playlist_container").height( height );

        $(".song_items .pos").width(20);
        $(".song_items .mime").width(35);
        $(".song_items .track").width(20);
        $(".song_items .func").width(20); // delete btn
        var width = context_content.width - 123; // leave 2px to avoid line wrap on some browsers, 25px for scrollbar
        $(".song_items .artist").width(width*0.24);
        $(".song_items .title" ).width(width*0.24);
        $(".song_items .album" ).width(width*0.24);
        $(".song_items .genre" ).width(width*0.24);
    }

    console.log("============ Playlist init =============");

    this.bind();
    this.update_viewport();

}

