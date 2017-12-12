$(document).ready(function(){
	$('.modal').draggable({
		//containment: 'document'	
	});
	$(document).on("click", function(event) {
		var target = $(event.target);
		if( target.hasClass('post-media')) {
			if (!target.parents('.modal').length){
				$('.modal').empty();
				target.clone().appendTo('.modal');
				var modalMedia = $('.modal').find('.post-media');
				modalMedia.addClass('modal-image');
				modalMedia.removeClass('post-image post-video')
				if (!target.is('video')) {
					$('.modal-image').css('max-width', window.innerWidth);
					$('.modal-image').on('DOMMouseScroll mousewheel wheel', function(e){
						if(e.originalEvent.detail > 0 || e.originalEvent.wheelDelta < 0) {
								$(this).css("width", "-=100");
								$(this).css('max-width', '-=100')
							} else {
								$(this).css('max-width', '+=100')
								$(this).css("width", "+=100");
							}
							return false;
					});
				} else {
					 $('.modal-image').attr('autoplay', '');
				}
			}
		} else {
			 $('.modal').empty();
			 $('.modal-image').css('width', '0px');
		}
	});
});
