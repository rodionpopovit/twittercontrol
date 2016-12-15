$(document).ready(function() {
    function dataUpdater(evt) {
        $.get('/tweetcontrol/tweetslogcontent/', {}, function(data) {
            $("#content").html(data);
            setTimeout(dataUpdater, 1000); // recall function every second
        });
    }

    dataUpdater(null);
});