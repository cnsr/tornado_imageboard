$(document).ready( function() {
	$('.fileinput').on("change", function(e) {
		if (this.files[0] != null) {
			var fileSize = this.files[0].size;
			if (fileSize > 5242880) {
				alert("File too large!");
				$('input[type="file"]').val(null);
				$('#text-area').prop('required',true);
			} else { $('#text-area').prop('required',false);}
		}
	});
});
