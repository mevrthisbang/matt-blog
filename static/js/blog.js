
const showToast = (
    message = "Sample Message",
    duration = 5000) => {

    let box = document.createElement("div");
    box.classList.add(
        "toast", `toast-danger`);
    box.innerHTML = ` <div class="toast-content-wrapper"> 
                      <div class="toast-icon"> 
                      <span class="material-symbols-outlined">error</span>
                      </div> 
                      <div class="toast-message">${message}</div> 
                      <div class="toast-progress"></div> 
                      </div>`;
    duration = duration || 5000;
    box.querySelector(".toast-progress").style.animationDuration =
            `${duration / 1000}s`;

    let toastAlready =
        document.body.querySelector(".toast");
    if (toastAlready) {
        toastAlready.remove();
    }

    document.body.appendChild(box)};


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

$('#search-textbox').on('keypress', function (e) {
         if(e.which === 13){
             window.location.href =  "/blog/search?keyword=" + e.target.value;
         }
});

async function authBlogContent(form) {
    event.preventDefault();
    var actionUrl = $(form).attr('action');
    var blogContent = document.getElementById("blog-content")
    $.ajax({
        type: "POST",
        url: actionUrl,
        data: $(form).serialize(), // serializes the form's elements.
        success: function (data) {
            if (data.canRead) {
                $(blogContent).html(data.content);
            } else {
                $(form).trigger("reset");
                showToast(data.content,5000);
            }
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