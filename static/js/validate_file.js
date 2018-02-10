$(document).ready( function() {
	$('.fileinput').on("change", function(e) {
		if (this.files[0] != null) {
			var fileSize = this.files[0].size;
			if (fileSize > 5242880) {
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
