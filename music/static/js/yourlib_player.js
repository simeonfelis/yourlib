function Player() {
    this.next = function() {
        player1.event_ended();
    }

    this.event_ended = function() {
        $.post("play/next", function(song_info) {
            if (song_info=="") {
                return;
            }
            else {
                player1.play_song(song_info);
            }
        });
    };

    this.play_song = function(song_info) {

        /* set src url */
        //if (song_info.dbg_file_path) {
        //    /* for debugging on localhost, I use a this to emulate x-accel-redirects */
        //    var $song_url='http://localhost:8080' + song_info.dbg_file_path;
        //}
        //else {
            var $song_url=base_url + "play/" + song_info.song_id; // song_base_url is defined in header (base.html)
        //}

        /* rebuild player (maybe firefox issue on invalid sources?) */
        $( "#player1" ).remove();
        $('<audio id="player1" controls="controls" preload="auto"></audio>').appendTo("#player1_temp");

        audio = document.createElement("audio");

        var can_play = false;
        if (song_info.mime == "audio/ogg") {
            var tmp = audio.canPlayType( "audio/ogg;" );
            if (tmp) {
                $('<source id="player1_ogg_source" src="' + $song_url + '" type="audio/ogg"></source>').appendTo("#player1");
                can_play = true;
            }

        }
        else if (song_info.mime == "audio/mp3") {
            var tmp = audio.canPlayType( "audio/mpeg;" );
            if (tmp) {
                $('<source id="player1_mp3_source" src="' + $song_url + '" type="audio/mp3"></source>').appendTo("#player1");
                can_play = true;
            }
        }
        if (can_play) {

            $( "#player1" ).bind("ended", this.event_ended);
            $( "#player1" )[0].pause();
            $( "#player1" )[0].load();
            $( "#player1" )[0].play();

            $( "#player1_song_info_title" ).html(song_info.title);
            $( "#player1_song_info_artist" ).html(song_info.artist);

            // maybe this should be just defined globally
            $( "#player1" ).attr("data-playlist_id", song_info['playlist_id']);
            $( "#player1" ).attr("data-item_id", song_info['item_id']);
            $( "#player1" ).attr("data-song_id", song_info['song_id']);
            $( "#player1" ).attr("data-source", song_info['source']);
            highlight_playing("Player.play_song()", "#content");
        }
        else {
            $( "#player1_song_info_title" ).html("Unsupported format");
            $( "#player1_song_info_artist" ).html(song_info.mime);
        }

    }
}
