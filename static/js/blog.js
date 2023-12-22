async function postComment(form) {
    event.preventDefault();
    var actionUrl = $(form).attr('action');
    var commentSection = document.getElementById("comment-section")
    $.ajax({
        type: "POST",
        url: actionUrl,
        data: $(form).serialize(), // serializes the form's elements.
        success: function (data) {
            $(commentSection).html(data);
            $(commentSection).append(data.response);
            $(form).trigger("reset");
        },
        beforeSend: function () {
            $('#loader').css("display", "block");
            $('#wrapper').css('webkit-filter', 'blur(20px)');
            $('#wrapper').css('filter', 'blur(20px)');
        },
        // hides the loader after completion of request, whether successfull or failor.
        complete: function () {
            $('#loader').css("display", "none");
            $('#wrapper').css('webkit-filter', 'blur(0px)');
        }
    });
    return true
}