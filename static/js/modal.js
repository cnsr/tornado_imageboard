$(document).ready(function(){
	if (localStorage.volume === null || localStorage.volume === '' || typeof localStorage.volume === 'undefined') {
		localStorage.volume = 0.5;
	}
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
				if (!target.is('video')){
					 $('.modal').find('img').attr('src', target.attr('data-image'));
				}
				//centering is broken
				centerModal();
				var modalMedia = $('.modal').find('.post-media');
				modalMedia.addClass('modal-image');
				modalMedia.removeClass('post-image post-video')
				if (!target.is('video')) {
					if ($('.modal-image')[0].naturalHeight >= window.innerHeight) {
						$('.modal').css('top', '0px');
						$('.modal-image').css('height', window.innerHeight + 'px');						
						$('.modal-image').css('width',$('.modal-image').width());
					}
					if ($('.modal-image').width() >= window.innerWidth) {
						$('.modal').css('left', '0px');
						$('.modal-image').css('width', $('.modal-image').width() + 'px');
						$('.modal-image').css('height',$('.modal-image').height());						
					}
					var aspect = aspectRatio($('.modal-image'));					
					var w = $('.modal-image').width() * aspect * 0.1;
					var h = $('.modal-image').height() * aspect * 0.1;
					centerModal();
					$('.modal-image').on('DOMMouseScroll mousewheel wheel', function(e){
						var win = $(window);
						formX = intify('left');
						formY = intify('top');
						lastCursorX = e.pageX - win.scrollLeft();
						lastCursorY = e.pageY - win.scrollTop();
						cursorInBoxPosX = lastCursorX-formX;
						cursorInBoxPosY = lastCursorY-formY;
						var nwu = ($(this).width() + w).toString();
						var nhu = ($(this).height() + h).toString();
						var nwd = ($(this).width() - w).toString();
						var nhd = ($(this).height() - h).toString();						
						if(e.originalEvent.detail > 0 || e.originalEvent.wheelDelta < 0) {
							$(this).css("width", nwd);
							$(this).css("height", nhd);
							moveForm(lastCursorX-cursorInBoxPosX, lastCursorY-cursorInBoxPosY);
						} else {
							$(this).css("width", nwu);
							$(this).css("height", nhu);
							moveForm(lastCursorX-cursorInBoxPosX, lastCursorY-cursorInBoxPosY);
						}
						return false;
					});
				} else {
					centerModal();
					var vid = $('.modal-image');
					vid.attr('autoplay', '');
					var vol = parseFloat(localStorage.volume);
					if (isNaN(vol)) {vol = 0.5};
					if (vol > 1.0) {vol = 1.0};
					if (vol < 0) {vol = 0.0};
					vid.prop('volume', parseFloat(vol));
					localStorage.volume = vol;
					vid.on('DOMMouseScroll mousewheel wheel', function(e){
						e.preventDefault();
						vol = parseFloat(localStorage.volume);
						if (vol > 1.0) {vol = 1.0};
						if (vol < 0) {vol = 0.0};
						vid.prop('volume', parseFloat(vol));
						if(e.originalEvent.detail > 0 || e.originalEvent.wheelDelta < 0) {
							var volume = (vol - 0.1);
							localStorage.volume = volume;
						} else {
							var volume = (vol + 0.1);
							localStorage.volume = volume;

						}
					});

				}
			}
		} else {
			$('.modal').empty();
			$('.modal-image').css('width', '0px');
		}
	});
	function centerModal() {
		var $form = $('.modal');
		var $fform = $form.find('.modal-image');
        var win = $(window);
        var windowWidth = win.width();
        var windowHeight = win.height();
        var formWidth = $fform.innerWidth();
        var formHeight = $fform.innerHeight();
		var x = Math.round(windowWidth / 2) - Math.round(formWidth / 2);
		var y = Math.round(windowHeight / 2) - Math.round(formHeight / 2);
        $form.css('top', y + 'px');
        $form.css('left', x + 'px');
	}

	function intify(shit) {
		return parseInt($('.modal').css(shit))
	}

	// broken if image exceeds window
	// replace forn W and H with image ones?
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

function aspectRatio(element) {
    return $(element).width() / $(element).height();
}
