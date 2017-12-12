$(function() {
    $('.post-image, .post-video').each(function() {
		var fid = $(this).parent().prev("div.info").attr('id');
		var file = $(this);
		var filename = file.attr('src');
		var h = file[0].naturalHeight;
		var w = file[0].naturalWidth;
		var filesize = sendAjax(filename, h, w, fid);
    });
});

$.ajaxSettings.traditional = true;
function sendAjax(file, h, w, fid) {
		fid = '#' + fid;
        $.ajax({
            url : "/ajax/file/", // the endpoint
            type : "POST", // http method
            data : {image: file, _xsrf: getCookie("_xsrf")}, // data sent with the post request
            // handle a successful response
            success : function(json) {
                var json = jQuery.parseJSON(json);
				if (h === undefined) {
					h = json.h;
					w = json.w;
				}

				var filedata = '<a href="' + file + '" class="filedata-a">' + json.file + '</a><p class="filedata-p">' + json.fileext + ', ' +  h + 'x' + w + ', ' + json.filesize;
				$(fid).append(filedata);
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
