function Yourlib() {
    this.logout = function() {
        var $data = {
            'csrfmiddlewaretoken': csrf_token,
        };
        $.post("accounts/logout/", $data, function() {
            window.location = "";
        });
    }
    this.rescan = function(event) {
        event.preventDefault();
        var url = $(this).attr("href");
        
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
                        $.post(url, data, function(rescan_status) {
                            yourlib.check_scan_status();
                        })
                        .success()
                        .error(function() {
                                $( "#rescan_status" ).html("Server Error? Wait...");
                                yourlib.check_scan_status(15000);
                        });


                        $( this ).dialog( "close" );
                    }
                }
            });
        }
        else{
            $("#btn_rescan_library").html("Cancel");
            $( "#rescan_status" ).html("Rescan requested. This might take a while....");

            var data = {"csrfmiddlewaretoken": csrf_token};
            $.post(url, data, function(rescan_status) {
                yourlib.check_scan_status();
            })
            .success()
            .error(function() {
                $( "#rescan_status" ).html("Server Error? Wait...");
                yourlib.check_scan_status(15000);
            });
        }
        return false; // don't do anything else
    }

    this.check_scan_status = function() {
        url = $("#btn_rescan_library").attr("href")
        $.get(url, function(rescan_status, status, xhr) {
            if (status != "success") {
                yourlib.bind_check_scan_timeout(15000);
            }
            else {
                $( "#rescan_status" ).html("Status: " + rescan_status);
                if ((rescan_status != "idle") && (rescan_status != "error") && (rescan_status != "")) {
                    $("#btn_rescan_library").html("Cancel");
                    yourlib.bind_check_scan_timeout();
                }
                else {
                    $("#btn_rescan_library").html("Rescan");
                }
            }
        })
        .error(function() {
            yourlib.bind_check_scan_timeout(15000);
        });
        return false;
    }
    this.bind_check_scan_timeout = function(timeout) {
        if (!window.check_scan_timeout_set) {
            window.check_scan_timeout_set = true;
            if (!timeout) {
                timout = 5000;
            }
            setTimeout(this.check_scan_status, timeout);
        }
    }
}
