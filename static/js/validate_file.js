$(document).ready( function() {
	$('.fileinput').on("change", function(e) {
		if (this.files[0] != null) {
			let maxfile = 20971520; //change this to desired filesize
			var fileSize = this.files[0].size;
			if (fileSize > maxfile) {
				$('.fileinput').val(null);
				$('#text-area').prop('required',true);
				$('.spoiler-div').hide();
				popUp("File too large!");				
			} else {
				$('#text-area').prop('required',false);
				$('.spoiler-div').show();				
			}
		}
	});
});
