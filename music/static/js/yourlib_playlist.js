function Playlist() {
    
    this.views = [];
    
    this.bind = function () {

        this.update_viewport();

        $(".btn").on("mouseenter", function(){$(this).addClass("ui-state-hover")});
        $(".btn").on("mouseleave", function(){$(this).removeClass("ui-state-hover")});


        $(".sortable").not(".song_item_heading").sortable( {
            items: "li:not(.song_item_heading, :not(.song_info))",
            start: function(event, ui) {
                $(ui.helper).addClass("ui-state-active");
            },
            stop: this.reorder,
            //activeClass: "ui-state-active",
            delay: 100,
        });
        $( ".sortable").disableSelection();

        highlight_playing("Playlist.bind()", target="#context_content");
    }

    this.reorder = function (event, ui) {
        /* callback when dragndrop stoped */
        /* when an element was reordered, this is called */

        // TODO: why is this not a jquery element?
        var $pl_item         = ui.item.get(0);
        var playlist_id      = $pl_item.getAttribute("data-playlist_id");
        var item_id          = $pl_item.getAttribute("data-item_id");
        if ($pl_item.previousElementSibling == null) {
            var item_previous_id = 0;
        }
        else {
            var item_previous_id = $pl_item.previousElementSibling.getAttribute("data-item_id");
        }
        var url = "playlist/reorder/";

        var $data = {
            'playlist_id'        : playlist_id,
            'item_id'            : item_id,
            'item_previous_id'   : item_previous_id,
        };

        // update playlist content. TODO: should be done with only one request!
        $( "#context_playlist_container" ).load(url, $data, function() {
            // our context is now document.window
            playlist.bind();
        })
        .error(function() {alert("error ordering playlist item");});
    }

    this.item_play = function () {
        /* will be called on clicks on items play btn in playlist */
        var data = {
            'song_id'            : $(this).attr("data-song_id"),
            'playlist_id'        : $(this).attr("data-playlist_id"),
            'item_id'            : $(this).attr("data-item_id"),
            'source'             : 'playlist',
        };
        $.post("play/", data, function(song_info) {
            player1.play_song(song_info);
        });
        return false; // Don't do anything else
    }

    this.item_remove = function() {
        /* will be called on clicks on items delete btn in playlists */
        var playlist_id = $(this).closest(".song_item").attr("data-playlist_id");
        var item_id     = $(this).closest(".song_item").attr("data-item_id");

        var url = "playlist/remove/" + playlist_id + "/" + item_id;

        // update playlist content. TODO: should be done with only one request!
        $( "#context_playlist_container" ).load(url, {}, function() {
            playlist.bind();
            // update number of playlists
            $( "#sidebar_playlists_content" ).load("sidebar/playlists/", function() {
                sidebar.bind();
            });
        })
        .error(function() {alert("error removing playlist item");});

        return false; // Don't do anything else
    }

    this.delete_list = function($playlist, confirmed) {
        /* will be called on clicks on delete btn of a playlist */

        if (confirmed === true) {
            // TODO: confirmation dialog
            var $data = {
                'playlist_id' : $playlist.attr("data-playlist_id"),
            };

            /* get new view for context */
            $( "#context_content" ).load("playlist/delete/", $data, function() {

                /* update playlists in sidebar */
                $( "#sidebar_playlists_content" ).load("sidebar/playlists/", function() {
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
        /* $(this) is expected to be a collection song item */
        var data = {
            "playlist_id" : playlist_id,
            "id" :          item_id,
            "source" :      source,
        };

        /* update number of playlist items in sidebar */
        // TODO: increase *only* number of playlist items in sidebar
        $( "#sidebar_playlists_content" ).load("playlist/append/", data, function() {
            sidebar.bind();
        });
    }
    this.create = function() {
        /* will be called on submit of create playlist field forms */
        var name = $.trim( $( "#playlist_create_name" ).val() );

        if ( !(name.length > 0) ) {
            console.log("Empty name for playlist");
            return false;
        }

        var $data = {
            'playlist_name': name,
        };
        $( "#sidebar_playlists_content" ).load("playlist/create/", $data, function() {
            $( "#playlist_create_name" ).val("");
            sidebar.bind();
        })
        .error(function() {alert("Error creating playlist");});

        return false; // Don't do anything else
    }

    this.exhibit = function(playlist_id, exhibit_finished_cb) {
        console.log("PLAYLIST EXHIBIT CALLED FOR PL " + playlist_id);

        this.exhibit_finished = exhibit_finished_cb;

        //this.active = "#context_playlist_id_" + playlist_id;
        this.active_id = playlist_id;
        //this.active_sidebar = "#sidebar_playlist_" + playlist_id;

        //is_loaded = $(this.active).length > 0;

        // fetch playlist
        $.post("playlist/", {"playlist_id": playlist.active_id}, function(data) {

            // store fetched data
            playlist.view = $(data).find("#context_playlist");

            // fade out whatever is just viewed
            $("#context_content").children().fadeOut("slow");
            // as there is usually more than one child in context_content,
            // wait until all fadeOuts are finished 
            $("#context_content").children().promise().done(function() {

                // remove eventually displayed playlist
                $("#context_playlist").remove();

                // highlight current in sidebar
                $("#sidebar").find(".currently_shown").removeClass("currently_shown");
                $(playlist.active_sidebar).addClass("currently_shown");

                // insert
                $("#context_content").append($(playlist.view).fadeIn("slow", function() {
                    // the exhibit process is finished here
                    playlist.exhibit_finished();
                }));

                // before fadeIn finishes, update the inserted effects
                playlist.update_viewport();
                playlist.bind();
            })
        });
/*
        if (is_loaded) {
            $("#context_content").children().fadeOut("slow", function() {
                $(playlist.active).fadeIn("slow", function() {playlist.exhibit_finished();});
                playlist.update_viewport();
            });
        }
        else {
            $.post("playlist/", {"playlist_id": playlist.active_id}, function(data) {
                $("#sidebar").find(".currently_shown").removeClass("currently_shown");
                $(playlist.active_sidebar).addClass("currently_shown");

                playlist.views["id_" + playlist.active_id] = $(data).find("#context_playlist");

                $("#context_content").children(":first").fadeOut("slow");

                setTimeout(function() {
                    $("#context_content").append(
                        $(playlist.views["id_" + playlist.active_id]).fadeIn("slow", function(){
                            playlist.exhibit_finished();
                        })
                    );
                }, 600);

                /*setTimeout(function() {
                    $("#context_content").append(
                        $(playlist.views["id_" + playlist.active_id])
                        .fadeIn("slow", function() {
                            playlist.exhibit_finished();
                        }
                    )});
                    
                    playlist.update_viewport();
                    playlist.bind();
                }); //*
            });
        }
        */
/*
        spinner_start($(this));

        $.post("playlist/",  {'playlist_id': playlist_id}, function(data) {
            playlist.exhibit(data);
            playlist.bind(); // for drag n drop
            spinner_stop("#sidebar");
            $("#sidebar").find(".currently_shown").removeClass("currently_shown");
            $("#sidebar_playlist_" + playlist.id).addClass("currently_shown");
        });



        if (data) {
            playlist.content = data;
        }
        if ($("#context_container").find("#context_content").length > 0) {
            $("#context_content").fadeOut(200, function() {
                $("#context_container").append($(playlist.content).fadeIn(500));
                $(this).remove();
                playlist.bind(); // for drag n drop
            });
        }
        else {
            $("#context_container").append($(playlist.content).fadeIn(500));
        }
        */
    }
    this.update_viewport = function() {
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
}

