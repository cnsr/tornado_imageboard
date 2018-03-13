$(document).ready( function() {
	$('.fileinput').on("change", function(e) {
		if (this.files[0] != null) {
			var fileSize = this.files[0].size;
			if (fileSize > 5242880) {
				$('#banner').val(null);
				popUp('File is too large!');
			}
			var img = new Image();
			img.src = window.URL.createObjectURL(this.files[0]);
			img.onload = function() {
				var width = img.naturalWidth,
					height = img.naturalHeight;

				window.URL.revokeObjectURL( img.src );

				if( width == 300 && height == 100 ) {
				}
				else {
					$('#banner').val(null);
					popUp("Banner should have 300x100 resolution!");					
				}
			};
		}
	});
	$('.banner-btn').on('click', function(e) {
		e.preventDefault();
		sendAjaxBannerDel(this);
	})
});
$.ajaxSettings.traditional = true;
function sendAjaxBannerDel(btn) {
	$.ajax({
		url : "/ajax/banner-del/",
		type : "POST",
		data : {brd: $(btn).attr('data-board'), banner: $(btn).attr('data-banner'), _xsrf: getCookie("_xsrf")},
		success : function(json) {
			popUp('Deleted');
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
