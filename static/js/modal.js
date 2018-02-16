var files = new Array();
$(document).ready(function(){
	$('.post-image, .post-video').each(function() {
		if (!$(this).hasClass('modal-image')) {
			var attr = $(this).attr('data-oid');
			files.push(attr);
		}
	});
	if (localStorage.volume === null || localStorage.volume === '' || typeof localStorage.volume === 'undefined') {
		localStorage.volume = 0.5;
	}
	var win = $(window);	
	$('.modal').draggable();
	$(document).on('click', '.modal-c', function(e) {
		e.preventDefault();		
		if (!$(this).is ('#modalC')) {
			var side = $(e.target).is('#modalL'); // true is left
			var current = $('.modal-image').attr('data-oid');
			if (side) {
				var next = files.indexOf(current) - 1;
			} else {
				var next = files.indexOf(current) + 1;
			}
			if (next > files.length - 1) next = 0;
			if (next < 0) next = files.length - 1;
			next = $('[data-oid=' + files[next] + ']');
			next.trigger('click');
		} else {
			var wH = $(window).height();
			var wW = $(window).width();
			moveForm(wW,wH,undefined);
			centerModal();
		}
	})
	$(document).on("click", function(event) {
		var target = $(event.target);
		if(target.hasClass('post-media')) {
			$('.modal-controls').css('display', 'block');
			if (!target.parents('.modal').length){
				$('.modal').empty();
				target.clone().appendTo('.modal');
				if (!target.is('video')){
					 $('.modal').find('img').attr('src', target.attr('data-image'));
				}
				//centering is broken, apparently, for images only, lol
				var modalMedia = $('.modal').find('.post-media');
				modalMedia.addClass('modal-image');
				modalMedia.removeClass('post-image post-video post-media');
				$('#modalC').trigger('click');				
				if (!target.is('video')) {
					// look into this shitcode it might need rewriting
					var aspect = aspectRatio($('.modal-image'));					
					var w = $('.modal-image').width() * aspect * 0.2;
					var h = $('.modal-image').height() * aspect * 0.2;
					centerModal();
					$('.modal-image').on('wheel', function(e){
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
						if(e.originalEvent.deltaY > 0) {
							$(this).css("width", nwd);
							$(this).css("height", nhd);
							moveForm(lastCursorX-cursorInBoxPosX, lastCursorY-cursorInBoxPosY, true);
						} else {
							$(this).css("width", nwu);
							$(this).css("height", nhu);
							moveForm(lastCursorX-cursorInBoxPosX, lastCursorY-cursorInBoxPosY, false);
						}
						return false;
					});
				} else if (target.is('audio')) {
					return false;
				} else {
					centerModal();
					var vid = $('.modal-image');
					vid.attr('autoplay', '');
					$(vid).on('loadeddata', function() {
						var vw = vid[0].videoWidth;
						var vh = vid[0].videoHeight;
						if (vw <= $(window).width() &&  vh <= $(window).height()) {
							vid.css('height', vh);
							vid.css('width', vw);
							centerModal();
						} else {
							vid.css('height', $(window).height());
							vid.css('width', $(window).width());
							centerModal();							 
						}
					});
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
			// horrible mess of if's
			if ($(target).parents().hasClass('modal')){
				if (!$(target).parents().hasClass('draggable')) {
					$('.modal').empty();
					$('.modal-image').css('width', '0px').attr('top', 0).attr('left', 0);
					$('.modal-controls').hide();
				}
			}
		}
	});
	function centerModal() {
		var $form = $('.modal');
		var url = $('.modal-image').attr('data-image');
		if (!$('.modal-image').is('video')) {
			$('<img/>').attr('src', url).on('load', function(){
				var img = {w:this.width, h:this.height};
				var win = $(window);
				var windowWidth = win.width();
				var windowHeight = win.height();
				var formWidth = img.w;
				var formHeight = img.h;
				var x = Math.round(windowWidth / 2) - Math.round(formWidth / 2);
				var y = Math.round(windowHeight / 2) - Math.round(formHeight / 2);
				if (windowWidth < formWidth) x = 0;
				if (windowHeight < formHeight) y = 0;
				if (x<0) x=0;
				if (y<0) y=0;
				$form.css('top', y + 'px');
				$form.css('left', x + 'px');
				if ($('.modal-image')[0].naturalHeight >= window.innerHeight) {
					$('.modal').css('top', '0px');
					$('.modal-image').css('height', window.innerHeight + 'px');						
					$('.modal-image').css('width',$('.modal-image').width());
				}
				else if ($('.modal-image').width() >= window.innerWidth) {
					$('.modal').css('left', '0px');
					$('.modal-image').css('width', $('.modal-image').width() + 'px');
					$('.modal-image').css('height',$('.modal-image').height());						
				}
			});
		} else {
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
	}

	function intify(shit) {
		return parseInt($('.modal').css(shit))
	}

	// broken if image exceeds window
	// replace form W and H with image ones?
	function moveForm(x, y, up) {
        var win = $(window);
		var $form = $('.modal');
        var windowWidth = win.width();
        var windowHeight = win.height();
        var formWidth = $form.innerWidth();
        var formHeight = $form.innerHeight();
		//if(x+formWidth > windowWidth) x = windowWidth-formWidth;
		//if(y+formHeight > windowHeight) y = windowHeight-formHeight;
		//if(x<0) x = 0;
		//if(y<0) y = 0;
		if (typeof up !== undefined) {
			if (up) {
				x +=  Math.round(formWidth*0.02);
				y += Math.round(formHeight*0.02);
			} else {
				x -=  Math.round(formWidth*0.02);
				y -= Math.round(formHeight*0.02);			 
			}
		}
		$form.css('top', y + 'px');
		$form.css('left', x + 'px');

		formX = x;
		formY = y;
    };
});

function aspectRatio(element) {
    return $(element).width() / $(element).height();
}

$.fn.draggable = function(){
    var $this = this,
	ns = 'draggable_'+(Math.random()+'').replace('.',''),
	mm = 'mousemove.'+ns,
	mu = 'mouseup.'+ns,
	$w = $(window),
	isFixed = ($this.css('position') === 'fixed'),
	adjX = 0, adjY = 0;		
	$this.mousedown(function(ev){
		if (!$(ev.target).is('textarea') && !$(ev.target).is('input') && !$(ev.target).is('button')) {
			var pos = $this.offset();
			if (isFixed) {
				adjX = $w.scrollLeft(); adjY = $w.scrollTop();
			}
			var ox = (ev.pageX - pos.left), oy = (ev.pageY - pos.top);
			$this.data(ns,{ x : ox, y: oy });
			$w.on(mm, function(ev){
				$this.addClass('draggable');
				ev.preventDefault();
				ev.stopPropagation();
				if (isFixed) {
					adjX = $w.scrollLeft(); adjY = $w.scrollTop();
				}
				var offset = $this.data(ns);
				$this.css({left: ev.pageX - adjX - offset.x, top: ev.pageY - adjY - offset.y, cursor: 'move'});
			});
			$w.on(mu, function(){
				$w.off(mm + ' ' + mu).removeData(ns);
				setTimeout(function() {
					$this.removeClass('draggable');
					$this.css('cursor', 'pointer');
				}, 250);
			});
		};

		return this;
	})
};
