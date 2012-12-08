
function Browse() {

    this.bind = function() {
        console.log("============ Browse bind =============");

        //this.layout = $('#context_browse_container').layout({ applyDefaultStyles: true });
        //this.layout.allowOverflow("south");
        //this.layout.allowOverflow("center");

        // bind all existing column elements
        this.bind_column_elements( $("#context_browse_artist_column .btn") );
        this.bind_column_elements( $("#context_browse_album_column .btn") );
        this.bind_column_elements( $("#context_browse_genre_column .btn") );
        this.bind_title_elements( $("#context_browse .song_item") );

        this.bind_title_pagination();
        this.bind_artist_pagination();
        this.bind_album_pagination();

        // settings button
        $("#btn_browse_settings")
        .off("click", this.on_settings_clicked)
        .on("click", this.on_settings_clicked);

    }

    this.bind_title_pagination = function () {
        this.titlePagination = new Pagination({
            scrollTarget : '#context_browse_title_container',
            appendTarget : "#context_browse_title_column",
            contentUrl   : base_url + "collection/browse/title/more/",
            contentData  : function() {return $("#context_browse .song_item").length;},
            beforeLoad   : function() {$('#loading_browse_title').fadeIn();},
            afterLoad    : function(newData) {
                if ($(newData).length > 0) {
                    $('#loading_browse_title').fadeOut();
                    browse.bind_title_elements(newData);
                    browse.update_viewport();
                }
                else {
                    $('#loading_browse_title').html("No more data");
                    $('#loading_browse_title').fadeOut();
                }
            },
            errorLoad    : function() {alert("Pagination load error title");},
            enabled      : true
        });
        // Don't show on default
        $('#loading_browse_title').fadeOut();
    }

    this.bind_genre_pagination = function () {
        this.genrePagination = new Pagination({
            scrollTarget : '#context_browse_genre_container',
            appendTarget : '#context_browse_genre_column',
            contentUrl   : base_url + "collection/browse/genre/more/",
            contentData  : function() {return $(".btn_browse_genre").length;},
            beforeLoad   : function() {$('#loading_browse_artist').fadeIn();},
            afterLoad    : function(newData) {
                console.log("TODO");
            },
            errorLoad    : function() {alert("Pagination load error for genre");},
            enabled      : true
        });
        // Don't show on default
        $('#loading_browse_genre').fadeOut();
    }
    this.bind_artist_pagination = function () {
        this.artistPagination = new Pagination({
            scrollTarget : '#context_browse_artist_container',
            appendTarget : "#context_browse_artist_column",
            contentUrl   : base_url + "collection/browse/artist/more/",
            contentData  : function() {return $(".btn_browse_artist").length;},
            beforeLoad   : function() {$('#loading_browse_artist').fadeIn();},
            afterLoad    : function(newData) {
                if ($(newData).length > 0) {
                    $('#loading_browse_artist').fadeOut();
                    browse.bind_column_elements(newData);
                    browse.update_viewport();
                }
                else {
                    $('#loading_browse_artist').html("No more data");
                    $('#loading_browse_artist').fadeOut();
                }
            },
            errorLoad    : function() {alert("Pagination load error for artist");},
            enabled      : true
        });
        // Don't show on default
        $('#loading_browse_artist').fadeOut();
    }

    this.bind_album_pagination = function () {
        this.albumPagination = new Pagination({
            scrollTarget : '#context_browse_album_container',
            appendTarget : "#context_browse_album_column",
            contentUrl   : base_url + "collection/browse/album/more/",
            contentData  : function() {return $(".btn_browse_album").length;},
            beforeLoad   : function() {$('#loading_browse_album').fadeIn();},
            afterLoad    : function(newData) {
                if ($(newData).length > 0) {
                    $('#loading_browse_album').fadeOut();
                    browse.bind_column_elements(newData);
                    browse.update_viewport();
                }
                else {
                    $('#loading_browse_album').html("No more data");
                    $('#loading_browse_album').fadeOut();
                }
            },
            errorLoad    : function() {alert("Pagination load error for album");},
            enabled      : true
        });
        $('#loading_browse_album').fadeOut();
    }

    this.song_play = function(e) {

        e.preventDefault();

        var url = "play/";

        var data = {
            'song_id': $(this).attr("data-song_id"),
            'source' : 'browse',
        };

        $.ajax({
            type:     "POST",
            url:      url,
            data:     data,
            success:  function(data, status, jqXHR) {
                player1.play_song(data);
            },
            error:    function(jqXHR, status, error) {
                // we are in context window again. sigh.
                console.log("ERROR PLAYING FROM BROWSE VIEW " + error);
            },
            complete:    function(jqXHR, textStatus) {
            },
        });

        return false; 
    }

    this.highlight = function() {
        $(this).addClass("ui-state-hover");
    }
    this.unlight = function() {
        $(this).removeClass("ui-state-hover");
    }

    this.bind_title_elements = function(titleElements) {

        $( titleElements )
        .off("click", this.song_play)
        .on("click", this.song_play)
        .draggable({
            items: "li:not(.song_item_heading, :not(.song_info))",
            helper: function(event) {
                artist = $(this).find(".artist").html();
                title = $(this).find(".title").html();
                song_id = $(this).attr("data-song_id");

                helper = $("<div class='ui-widget-content ui-state-focus ui-corner-all'></div>");
                helper.html(artist + " - " + title);

                helper.attr("data-song_id", song_id);
                helper.attr("data-source", "collection");
                return $( helper );
            },
            appendTo: "body",
            containment: "document",
            revert: "invalid",
            delay: 100,
        })
        .disableSelection()
        .off("mouseenter", this.highlight)
        .off("mouseleave", this.unlight)
        .on("mouseenter",  this.highlight)
        .on("mouseleave",  this.unlight);
    }

    this.bind_column_elements = function(columnElements) {
        // will bind effects only for items in columnElements

        $( columnElements )
        .on("click", function(e) {

            var column = $(this).parent().find(".ui-widget-header").html();

            console.log("bind_column_elements: item clicked in column " + column);

            // mark/unmark for selection
            if (!e.ctrlKey) {
                was_selected = $(this).hasClass("selected");
                amount = $(this).parent().find(".selected").length

                // remove other selections in column
                $(this).parent().find(".selected").removeClass("selected");

                if (!was_selected) {
                    // if it was not selected, make it the new selected item
                    $(this).addClass("selected");
                }
                else {
                    // if it was selected, keep it selected, but only if multiple
                    // items were selected
                    if (amount > 1) {
                        $(this).addClass("selected");
                    }
                }
            }
            else {
                $(this).toggleClass("selected");
                // toggle selection
                //if ($(this).hasClass("selected")) {
                //    $(this).removeClass("selected")
                //}
                //else{
                //    $(this).addClass("selected")
                //}
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

                    helper.attr("data-item_id", artist_id);
                    count = $(this).find(".count").html();

                    helper.html("All songs (" + count + ") from artist <br />" + artist);

                    return $( helper );
                }
                else if ("album" == column) {
                    album = $(this).find(".name").html();
                    album_id = $(this).attr("data-album_id");

                    helper.attr("data-item_id", album_id);
                    count = $(this).find(".count").html();

                    helper.html("All songs (" + count + ") in album <br />" + album);

                    return $( helper );
                }
                else if ("genre" == column) {
                    console.log("TODO");
                }
                else if ("title" == column) {
                    song_id = $(this).attr("data-title_id");
                    helper.html("Song: " + $(this).html());
                    helper.attr("data-item_id", song_id);

                    return $( helper );
                }
            },
            appendTo: "body",
            containment: "document",
            revert: "invalid",
            delay: 100,
        })
        .disableSelection()
        .on("mouseenter", function() {
            $(this).addClass("ui-state-hover");
        })
        .on("mouseleave", function() {
            $(this).removeClass("ui-state-hover");
        });
        /*.on("mouseenter", function() {
            // TODO: make this optinal
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
    }

    this.on_column_received = function(data) {
        // callback for received data when a column item was selected. This could be
        // data for any column, so I have to find out what I just received.
        var $album_container  = $(data).find("#context_browse_album_container");
        var $genre_container  = $(data).find("#context_browse_genre_container");
        var $title_container  = $(data).find("#context_browse_title_container");
        var $artist_container = $(data).find("#context_browse_artist_container");

        // the server tells me which column was clicked to receive this
        // data. This information is in a hidden element. Currently not used/required.
        var column_from = $(data).find("#column_from").html();

        if ($artist_container.length > 0) {
            // replace old artist column
            if ($("#context_container").find("#context_browse_artist_container").length > 0) {
                $("#context_browse_artist_container").replaceWith($artist_container);

                // bind effects only for items in this column
                browse.bind_column_elements( $("#context_browse_artist_column .btn") );

                // we removed the scrolled window. rebind scroll pagination!
                browse.bind_artist_pagination();
            }
        }

        if ($album_container.length > 0) {
            // replace old album column
            if ($("#context_container").find("#context_browse_album_container").length > 0) {
                $("#context_browse_album_container").replaceWith($album_container);

                // bind effects only for items in this column
                browse.bind_column_elements( $("#context_browse_album_column .btn") );

                // we removed the scrolled window. rebind scroll pagination!
                browse.bind_album_pagination();
            }
        }

        if ($title_container.length > 0) {
            // replace old title column
            if ($("#context_container").find("#context_browse_title_container").length > 0) {
                $("#context_browse_title_container").replaceWith($title_container);

                // bind effects only for items in this column
                browse.bind_column_elements( $("#context_browse_title_column .btn") );

                // we removed the scrolled window. rebind scroll pagination!
                browse.bind_title_pagination();
            }
        }

        if ($genre_container.length > 0) {
            console.log("TODO");
        }
        if ($artist_container.length > 0) {
            console.log("TODO");
        }

        browse.update_viewport();
    }

    this.on_column_item_clicked = function(column_from) {

        // if a song title was clicked, play it.
        if ("title" == column_from) {
            return;
        }

        // if something else was clicked, select it
        var selected = $("#context_browse_" + column_from + "_column .selected").get();
        var item_ids = [];
        for (item in selected) {
            item_ids.push($(selected[item]).attr("data-" + column_from + "_id"));
        }

        var data = {
            'items' : item_ids,
        }

        $.post(base_url + 'collection/browse/' + column_from + '/', data, browse.on_column_received);
    }

    this.on_settings_clicked = function() {
        //$( "#dialog-confirm-playlist-delete" ).find(".playlist_name").html($(this).attr("data-playlist_name"));

            var data = {};

            var url = base_url + "settings/collection/browse/";

            $.ajax({
                type:     "GET",
                url:      url,
                data:     data,
                success:  function(data, status, jqXHR) {
                    // we are in context window again. sigh.
                    $form = $(data).find("#dialog-browse-settings-colums-data");

                    // remove evtually existing form
                    $("#dialog-browse-settings-colums-data").remove();
                    $("#dialog-browse-settings-colums-container").append($form).fadeIn("slow");

                    // show dialog
                    $( "#dialog-browse-settings" ).dialog({
                        resizable: true,
                        height:500,
                        width:600,
                        modal: true,
                        buttons: {
                            "Save": function() {
                                $( this ).dialog( "close" );
                            },
                            "Cancel": function() {

                                //browse.save_settings($playlist=$this, confirmed=true);

                                $( this ).dialog( "close" );
                            }
                        }
                    });

                },
                error:    function(jqXHR, status, error) {
                    // we are in context window again. sigh.
                    console.log("ERROR FETCHING BROSESE SETTINGS");
                },
                complete:    function(jqXHR, textStatus) {
                },
                datatype: "html"
            });
    }

    this.exhibit = function(exhibit_finished_cb) {

        this.exhibit_finished = exhibit_finished_cb;

        is_loaded = $("#context_browse").length > 0;

        if (is_loaded) {
            $("#context_content").children().fadeOut("fast");
            $("#context_content").children().promise().done(function() {
                $("#context_browse").fadeIn("fast", function() {
                    // the exhibit process is finished here
                    browse.exhibit_finished();
                });
                highlight_playing("browse.exhibit()", "#context_browse");
                browse.update_viewport();
            });
        }
        else {

            var data = {};

            var url = base_url + "collection/browse/";

            $.ajax({
                type:     "GET",
                url:      url,
                data:     data,
                success:  function(data, status, jqXHR) {
                    // we are in context window again. sigh.

                    $("#sidebar").find(".currently_shown").removeClass("currently_shown");
                    $("#btn_sidebar_browse").addClass("currently_shown");

                    browse.view = $(data).find("#context_browse");

                    $("#context_content").children().fadeOut("slow");
                    $("#context_content").children().promise().done(function() {
                        $("#context_content").append($(browse.view).fadeIn("slow", function() {
                            // the exhibit process is finished here
                            browse.exhibit_finished();
                        }));
                        highlight_playing("browse.exhibit()", "#context_browse");
                        browse.update_viewport();
                        browse.bind();
                    });

                },
                error:    function(jqXHR, status, error) {
                    // we are in context window again. sigh.
                    console.log("ERROR SHOWING COLLECTION");
                },
                complete:    function(jqXHR, textStatus) {
                },
                datatype: "html"
            });
        }
    }

    this.update_viewport = function() {

        console.log("============ Browse update_viewport =============");

        if ($.find("#context_browse_container").length == 0) {
            // nothing to update
            return;
        }

        var height = context_content.height - $("#context_header").height();
        $("#context_browse_columns").height(height/2 - 2);
        $("#context_browse_artist_container").height( height/2 -2 );
        $("#context_browse_album_container").height( height/2 - 2 );
        $("#context_browse_genre_container").height( height/2 - 2);
        $("#context_browse_title_container").height( height/2 - 2);
        var width = context_content.width*0.33 - 3;
        $(".browse_column").width( width );
        //$("#context_browse_artist_column .count").width(20); -> css
        $("#context_browse_artist_column .name").width(width-40); // scroll bar and count
        $("#context_browse_album_column .name").width(width-40); // scroll bar and count
        $("#context_browse_title_column .name").width(width-70); // scroll bar, track number and length and padding

    }

    console.log("============ Browse init =============");

    this.bind();
    this.update_viewport();

}
