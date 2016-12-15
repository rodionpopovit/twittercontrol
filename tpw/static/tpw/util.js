$(document).ready(function() {
    var tagsUpdater = function(evt) {
        var rule_id = $("#ruleoption option:selected").prop('value');
        $.get('/tweetcontrol/querytokens/', {'rule': rule_id}, function(data) {
            $("#resulttags").html(data);
        });
    }

    $("#ruleoption").change(tagsUpdater);
    $("#btntesttweet").click(function() {
        var com_id = $("#communityoption option:selected").prop('value');
        var rule_id = $("#ruleoption option:selected").prop('value');
        var msg = $("#requiredmessage").val();
        var date = $("#datepicker").val();

        $.get('/tweetcontrol/testtweet/', {'rule': rule_id, 'community': com_id, 'message': msg, 'date': date}, function(data) {
            $("#testingresult").html(data);
        });
    });

    tagsUpdater($("#ruleoption option:selected").prop('value'));
});

function addTag(tag) {
    document.getElementById("requiredmessage").value += tag;
}