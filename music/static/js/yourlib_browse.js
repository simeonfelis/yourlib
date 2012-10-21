
function Browse() {

    this.bind = function(selector) {
        console.log("============ Browse bind =============");

        // bind all existing column elements
        this.bindColumnElements( $("#context_browse_artist_column .btn") );
        this.bindColumnElements( $("#context_browse_album_column .btn") );
        this.bindColumnElements( $("#context_browse_genre_column .btn") );
        this.bindColumnElements( $(".btn_browse_title") );

        this.bind_title_pagination();
        this.bind_artist_pagination();
        this.bind_album_pagination();
    }

    this.bind_title_pagination = function () {
        this.titlePagination = new Pagination({
            scrollTarget : '#context_browse_title_container',
            appendTarget : "#context_browse_title_column",
            contentUrl   : base_url + "collection/browse/title/",
            contentData  : function() {return $(".btn_browse_title").length;},
            beforeLoad   : function() {$('#loading_browse_title').fadeIn();},
            afterLoad    : function(newData) {
                if ($(newData).length > 0) {
                    $('#loading_browse_title').fadeOut();
                    browse.bindColumnElements(newData);
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
    }

    this.bind_artist_pagination = function () {
        this.artistPagination = new Pagination({
            scrollTarget : '#context_browse_artist_container',
            appendTarget : "#context_browse_artist_column",
            contentUrl   : base_url + "collection/browse/artist/",
            contentData  : function() {return $(".btn_browse_artist").length;},
            beforeLoad   : function() {$('#loading_browse_artist').fadeIn();},
            afterLoad    : function(newData) {
                if ($(newData).length > 0) {
                    $('#loading_browse_artist').fadeOut();
                    browse.bindColumnElements(newData);
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
    }

    this.bind_album_pagination = function () {
        this.albumPagination = new Pagination({
            scrollTarget : '#context_browse_album_container',
            appendTarget : "#context_browse_album_column",
            contentUrl   : base_url + "collection/browse/album/",
            contentData  : function() {return $(".btn_browse_album").length;},
            beforeLoad   : function() {$('#loading_browse_album').fadeIn();},
            afterLoad    : function(newData) {
                if ($(newData).length > 0) {
                    $('#loading_browse_album').fadeOut();
                    browse.bindColumnElements(newData);
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
    }

    this.bindColumnElements = function(columnElements) {
        // will bind effects only for items in columnElements

        $( columnElements )
        .on("click", function(e) {

            var column = $(this).parent().find(".ui-widget-header").html();

            console.log("bindColumnElements: item clicked in column " + column);

            if ("title" == column) {
                // treat click on song titles different

                var $data = {
                    'song_id': $(this).attr("data-title_id"),
                    'source' : 'browse',
                };
                $.post("play/", $data, function(song_info) {
                    player1.play_song(song_info);
                });
                return false; 

            }
            else {
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
            }

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
        // data. This information is in a hidden element. Currently not used.
        var column_from = $(data).find("#column_from").html();

        if ($album_container.length > 0) {
            // replace old album column
            if ($("#context_container").find("#context_browse_album_container").length > 0) {
                $("#context_browse_album_container").replaceWith($album_container);

                // bind effects only for items in this column
                browse.bindColumnElements( $("#context_browse_album_column .btn") );

                // we removed the scrolled window. rebind scroll pagination!
                browse.bindAlbumPagination();
            }
        }

        if ($title_container.length > 0) {
            // replace old title column
            if ($("#context_container").find("#context_browse_title_container").length > 0) {
                $("#context_browse_title_container").replaceWith($title_container);

                // bind effects only for items in this column
                browse.bindColumnElements( $("#context_browse_title_column .btn") );

                // we removed the scrolled window. rebind scroll pagination!
                browse.bindTitlePagination();
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

        var height = context_content.height - $("#context_header").height() - 1;
        $("#context_browse_artist_container").height( height );
        $("#context_browse_album_container").height( height );
        $("#context_browse_title_container").height( height );
        var width = context_content.width*0.32 - 1;
        $(".browse_column").width( width );

    }

    console.log("============ Browse init =============");

    this.bind();
    this.update_viewport();

}
