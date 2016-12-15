$(document).ready(function() {
    function dataUpdater(evt) {
        $.get('/tweetcontrol/outboxcontent/', {}, function(data) {
            $("#content").html(data);
            setTimeout(dataUpdater, 1000); // recall function every second
        });
    }

    dataUpdater(null);

    $("#btnpausesending").click(function(evt) {
        alert('test');
    });
});

function pauseSending() {
    $.get('/tweetcontrol/pausesending/');
}