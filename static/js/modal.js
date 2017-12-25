$(document).ready(function(){
	centerModal();	
	var win = $(window);	
	$('.modal').draggable({
	});
	$(document).on("click", function(event) {
		var target = $(event.target);
		if( target.hasClass('post-media')) {
			if (!target.parents('.modal').length){
				$('.modal').empty();
				target.clone().appendTo('.modal');
				centerModal();
				var modalMedia = $('.modal').find('.post-media');
				modalMedia.addClass('modal-image');
				modalMedia.removeClass('post-image post-video')
				if (!target.is('video')) {
					$('.modal-image').css('max-width', window.innerWidth);
					$('.modal-image').on('DOMMouseScroll mousewheel wheel', function(e){
						var win = $(window);
						formX = intify('left');
						formY = intify('top');
						lastCursorX = e.pageX - win.scrollLeft();
						lastCursorY = e.pageY - win.scrollTop();
						cursorInBoxPosX = lastCursorX-formX;
						cursorInBoxPosY = lastCursorY-formY;
						if(e.originalEvent.detail > 0 || e.originalEvent.wheelDelta < 0) {
							$(this).css("width", "-=100");
							$(this).css('max-width', '-=100');
							moveForm(lastCursorX-cursorInBoxPosX, lastCursorY-cursorInBoxPosY);
						} else {
							$(this).css('max-width', '+=100')
							$(this).css("width", "+=100");
							moveForm(lastCursorX-cursorInBoxPosX, lastCursorY-cursorInBoxPosY);
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
	function centerModal() {
		var $form = $('.modal');
        var win = $(window);
        var windowWidth = win.width();
        var windowHeight = win.height();
        var formWidth = $form.innerWidth();
        var formHeight = $form.innerHeight();
		var x = Math.round(windowWidth / 2) - Math.round(formWidth / 2);
		var y = Math.round(windowHeight / 2) - Math.round(formHeight / 2);
        $form.css('top', y + 'px');
        $form.css('left', x + 'px');
	}

	function intify(shit) {
		return parseInt($('.modal').css(shit))
	}

	function moveForm(x, y) {
        var win = $(window);
		var $form = $('.modal');
        var windowWidth = win.width();
        var windowHeight = win.height();
        var formWidth = $form.innerWidth();
        var formHeight = $form.innerHeight();

		if(x+formWidth > windowWidth) x = windowWidth-formWidth;
		if(y+formHeight > windowHeight) y = windowHeight-formHeight;
		if(x<0) x = 0;
		if(y<0) y = 0;


		$form.css('top', y + 'px');
		$form.css('left', x + 'px');

		formX = x;
		formY = y;
    };
});
