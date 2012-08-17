function Upload() {
    this.bind = function() {
        /* check if there are uploads ongoing */
        if ($("li", "#upload_status_content" ).length != 0 ) {
            this.bind_check_status_timeout();
        }

        /* make use of the XMLHttpRequest (Level 2) features from the form
         * plugin. This will probably not work with Opera.
         */

        var bar = $('.bar');
        var percent = $('.percent');
        var status = $('#status');


        $('#upload_form').ajaxForm({
            beforeSend: function() {
                status.empty();
                var percentVal = '0%';
                bar.width(percentVal)
                percent.html(percentVal);
            },
            uploadProgress: function(event, position, total, percentComplete) {
                var percentVal = percentComplete + '%';
                bar.width(percentVal)
                percent.html(percentVal);
            },
            complete: function(xhr) {
                status.html(xhr.responseText);
            }
        }); 

    }

    this.bind_check_status_timeout = function() {
        setTimeout(this.check_status, 1000);
    }

    this.check_status = function() {
        $( "#upload_status_content" ).load("upload/", function() {
            // attention: we are now not in Upload, but document.window!
            if ($("li", "#upload_status_content" ).length != 0) {
                upload.bind_check_status_timeout();
            }
        });
    }
}
