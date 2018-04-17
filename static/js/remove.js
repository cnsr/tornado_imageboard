$(document).ready(function() {
	$(document).on('click', '.del', function(){
		var id = $(this).attr('data-id');
		sendAjaxRemove(id);
		popUp('Post has been deleted.');
	});
	$(document).on('click', '.post-info', function(){
		var id = $(this).attr('data-id');
		askInfoAjax(id);		 
	})
});
$.ajaxSettings.traditional = true;
function sendAjaxRemove(id) {
        $.ajax({
            url : "/ajax/remove/",
            type : "POST",
            data : {post: id, _xsrf: getCookie("_xsrf")},
            success : function(json) {
                var json = jQuery.parseJSON(json);
				if (json.op == 'true') {
					window.location.replace($(location).attr('href').split('/').slice(0,-2).join('/'));
				} else {
					$('#' + id).fadeOut('slow');					
				}
            },
            error : function(xhr,errmsg,err) {
                console.log(xhr.status + ": " + xhr.responseText);
            }
        });
    };

function askInfoAjax(id) {
        $.ajax({
            url : "/ajax/info/",
            type : "POST",
            data : {post: id, _xsrf: getCookie("_xsrf")},
            success : function(json) {
				popUp(json);
            },
            error : function(xhr,errmsg,err) {
                console.log(xhr.status + ": " + xhr.responseText);
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
