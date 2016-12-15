$(document).ready(function() {
    var tagsUpdater = function(evt) {
        var zone_val = $("#tzdata option:selected").prop('value');
        $.get('/tweetcontrol/getcountrytimezones/' + zone_val + '/', {}, function(data) {
            $("#tzstate").html(data);
        });
    }

    $("#tzdata").change(tagsUpdater);
});