$('form input').change(function() {
    $(this).closest('form').submit();
});

$("form").on("submit", function(e) {
    var name = $(this).attr("name");
    if (name.includes("toggle_")) {
        var prediction_id = name.substring(7);
        $.ajax({
            type: "POST",
            url: "/prediction/toggle/" + prediction_id
        });
        e.preventDefault();
    };        
});