$(document).ready(function() {
	$('.del').on('click', function(){
		var id = $(this).attr('data-id');
		sendAjaxRemove(id);
	});
});
$.ajaxSettings.traditional = true;
function sendAjaxRemove(id) {
        $.ajax({
            url : "/ajax/remove/", // the endpoint
            type : "POST", // http method
            data : {post: id, _xsrf: getCookie("_xsrf")}, // data sent with the post request
            // handle a successful response
            success : function(json) {
                var json = jQuery.parseJSON(json);
				if (json.op == 'true') {
					window.location.replace($(location).attr('href').split('/').slice(0,-2).join('/'));
				} else {
					var post = $('#' + id);
					post.remove();
				}
            },

            // handle a non-successful response
            error : function(xhr,errmsg,err) {
                console.log(xhr.status + ": " + xhr.responseText);
                // provide a bit more info about the error to the console
            }
        });
    };

function getCookie(c_name)
{
	if (document.cookie.length > 0)
	{
		c_start = document.cookie.indexOf(c_name + "=");
		if (c_start != -1)
		{
			c_start = c_start + c_name.length + 1;
			c_end = document.cookie.indexOf(";", c_start);
			if (c_end == -1) c_end = document.cookie.length;
			return unescape(document.cookie.substring(c_start,c_end));
		}
	}
	return "";
};
