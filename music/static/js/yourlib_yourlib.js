function Yourlib() {
    this.logout = function() {
        var $data = {
            'csrfmiddlewaretoken': csrf_token,
        };
        $.post("accounts/logout/", $data, function() {
            window.location = "";
        });
    }
    this.rescan = function() {
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
                        $.post("rescan", data, function(rescan_status) {
                            yourlib.check_scan_status();
                        })
                        .success()
                        .error(function() { $( "#rescan_status" ).html("Server Error?"); });

                        $( this ).dialog( "close" );
                    }
                }
            });
        }
        else{
            $("#btn_rescan_library").html("Cancel");
            $( "#rescan_status" ).html("Rescan requested. This might take a while....");

            var data = {"csrfmiddlewaretoken": csrf_token};
            $.post("rescan", data, function(rescan_status) {
                yourlib.check_scan_status();
            })
            .success()
            .error(function() { $( "#rescan_status" ).html("Server Error?"); });
        }
        return false; // don't do anything else
    }

    this.check_scan_status = function() {
        $.get("rescan", function(rescan_status) {
            $( "#rescan_status" ).html("Status: " + rescan_status);
            if ((rescan_status != "idle") && (rescan_status != "error") && (rescan_status != "")) {
                $("#btn_rescan_library").html("Cancel");
                yourlib.bind_check_scan_timeout();
            }
            else {
                $("#btn_rescan_library").html("Rescan");
            }
        });
        return false;
    }
    this.bind_check_scan_timeout = function() {
        setTimeout(this.check_scan_status, 5000);
    }
}
