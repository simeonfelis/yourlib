function Upload() {
    this.checking = false;

    this.bind = function() {
        
        //$("#upload_progress_bar").progressbar({value: 0});

        $("#upload_clear_pending").on("click", function() {
            $.post("upload/clearpending/", {}, function() {});
        })
        /* check if there are uploads ongoing */
        if ($("li", "#upload_status_content" ).length != 0 ) {
            this.bind_check_status_timeout();
        }

        /* make use of the XMLHttpRequest (Level 2) features from the form
         * plugin. This will probably not work with Opera.
         */

        var bar = $('.bar');
        var percent = $('.percent');
        //var status = $('#upload_status');
        var progress = $(".progress");


        $('#upload_form').ajaxForm({
            beforeSend: function() {
                progress.slideDown("fast");
                upload.bind_check_status_timeout();
                //status.empty();
                var percentVal = '0%';
                bar.width(percentVal)
                //$("#upload_progress_bar").value(0);
                percent.html(percentVal);
            },
            uploadProgress: function(event, position, total, percentComplete) {
                var percentVal = percentComplete + '%';
                bar.width(percentVal)
                percent.html(percentVal);
                //$("#upload_progress_bar").progressbar("value", percentComplete);
            },
            complete: function(xhr) {
                progress.slideUp("fast");
                //var received_status = $(xhr.responseText).find("#upload_status");
                //$('#upload_status').replaceWith(xhr.responseText);
                upload.bind_check_status_timeout();
                //status.html(xhr.responseText);
            }
        }); 

    }
    
    this.update_viewport = function() {
        context_content.update_viewport();
        var height = context_content.height - $("#context_header").height() - 1;
        $("#context_upload_container").height( height );
    }

    this.exhibit = function(exhibit_finished_cb) {


        this.exhibit_finished = exhibit_finished_cb;

        is_loaded = $("#context_upload").length > 0;

        if (is_loaded) {
            $("#context_content").children().fadeOut("fast");
            $("#context_upload").children().promise().done(function() {
                $("#context_upload").fadeIn("fast", function() {
                    // the exhibit process is finished here
                    upload.exhibit_finished();
                });
                upload.bind_check_status_timeout();
                upload.update_viewport();
            });
        }
        else {
            $.post("upload/show/", {}, function(data) {
                $("#sidebar").find(".currently_shown").removeClass("currently_shown");
                $("#btn_sidebar_upload").addClass("currently_shown");

                upload.view = $(data).find("#context_upload");

                $("#context_content").children(":first").fadeOut("slow");
                $("#context_content").children(":first").promise().done(function() {
                    $("#context_content").append($(upload.view).fadeIn("slow", function() {
                        // the exhibit process is finished here
                        upload.exhibit_finished();
                    }));
                    upload.update_viewport();
                    upload.bind();
                });
            });
        }
    }

    this.bind_check_status_timeout = function() {
        if (!this.checking) {
            this.checking = true;
            setTimeout(this.check_status, 3000);
        }
    }

    this.check_status = function() {
        if ($("#context_upload").is(":visible")) {
            $( "#upload_status_content" ).load("upload/status/", function() {
                upload.checking = false;
                // attention: we are now not in Upload, but document.window!
                if ($("li", "#upload_status_content" ).length != 0) {
                    upload.bind_check_status_timeout();
                    upload.check_pending();
                }
            });
        }
    }

    this.check_pending = function() {
        $("li", "#upload_status_content" ).each(function() {
            if ($(this).html().indexOf("pending") > 0 ) {
                $("#upload_clear_pending").show();
                $("#upload_clear_pending")
                .on("mouseenter", function(){$(this).addClass("ui-state-hover")})
                .on("mouseleave", function(){$(this).removeClass("ui-state-hover")})
                .on("click", function() {
                    $.post("upload/clearpending/", {}, function() {});
                })
            }
            else {
                $("#upload_clear_pending").hide();
            }
        })
    }
}
