var files = new Array;
//  this relies on the fact that there's only a single draggable element around 
var initX, initY, firstX, firstY;

const processModalClick = (e) => {
	e.preventDefault();		
	console.log('clicked on a button:', e.target)
	if (!e.target.id === 'modalC') {
		let side = e.target.id === 'modalL'; // true is left
		let current = document.getElementsByClassName('modal-image')[0].getAttribute('src');
		let current_index = files.indexOf(current);
		let next_index = 0;
		if (side) next_index = current_index - 1;
		if (!side) next_index = current_index + 1;
		if (next_index < 0) next_index = files.length - 1;
		if (next_index > files.length - 1) next_index  = 0;
		fnext = files[next_index];
		let next_image = document.querySelectorAll(`*[data-image="${fnext}"]`)[0];
		if (!next_image.length == 1) {
			next_image = document.querySelectorAll(`video[src="${fnext}"]`)[0];
		}
		let post = next_image.closest('.oppost, .thread-outer, .post, .preview-post');
		[...document.getElementsByClassName('focused')].map(el => el.classList.remove('focused'))
		// TODO: scroll without the JQuery
		$('html,body').animate({
			scrollTop: post.offset().top
		}, 1);
		post.classList.add('focused');
		// TODO: figure out how to trigger click using plain js
		$(`#${next_image.id}`).trigger('click');
	} else {
		// var wH = $(window).height();
		// var wW = $(window).width();
		// moveForm(wW,wH,undefined);
		centerModal();
	}
};

const moveForm = (x, y, up) => {
	console.log('moveForm', x, y, up)
	// var win = $(window);
	let modalElement = document.getElementsByClassName('modal')[0];
	// var windowWidth = win.width();
	// var windowHeight = win.height();
	// TODO: replace this atrocity
	var formWidth = modalElement.style.width;
	var formHeight = modalElement.style.height;
	//if(x+formWidth > windowWidth) x = windowWidth-formWidth;
	//if(y+formHeight > windowHeight) y = windowHeight-formHeight;
	//if(x<0) x = 0;
	//if(y<0) y = 0;
	if (typeof up !== undefined) {
		if (up) {
			x +=  Math.round(formWidth*0.01);
			y += Math.round(formHeight*0.01);
		} else {
			x -=  Math.round(formWidth*0.01);
			y -= Math.round(formHeight*0.01);			 
		}
	}
	modalElement.style.top = `${y}px`;
	modalElement.style.left = `${x}px`;

	formX = x;
	formY = y;
};

const mouseDown = (e) => {
	console.log('mouseDown', e)
	e.preventDefault();
	let target = e.target;

	initX = target.offsetLeft;
	initY = target.offsetTop;

	firstX = e.pageX;
	firstY = e.pageY;

	target.addEventListener('mousemove', mouseMove, false);

	window.addEventListener('mouseup', (event) => {
		target.removeEventListener('mouseMove', mouseMove, false);
	})
}

const mouseMove = (e) => {
	console.log('mouseMove', e)
	e.target.style.left = `${initX + e.pageX - firstX}px`;
	e.target.style.top = `${initY + e.pageY - firstY}px`;
}


const centerModal = () => {
	console.log('CENTER')
	var modalElement = document.getElementsByClassName('modal')[0];
	var modalImage = document.getElementsByClassName('modal-image')[0]
	var url = modalImage.getAttribute('data-image');
	if (modalImage.tagName !== 'video') {
		modalImage.src = url;
		modalImage.id = 'centeredImage'
		modalImage.addEventListener('load', e => {
			var x = Math.round(window.innerWidth / 2) - Math.round(e.target.width / 2);
			var y = Math.round(window.innerHeight / 2) - Math.round(e.target.height / 2);
			if (window.innerWidth < e.target.width) x = 0;
			if (window.innerHeight < e.target.height) y = 0;
			if (x<0) x=0;
			if (y<0) y=0;
			modalElement.style.top = `${y}px`;
			modalElement.style.left = `${x}px`;
			// error here becasue of naturalheight
			// if ($('.modal-image')[0].naturalHeight >= window.innerHeight) {
			// 	$('.modal').css('top', '0px');
			// 	$('.modal-image').css('height', window.innerHeight + 'px');
			// 	$('.modal-image').css('width',$('.modal-image').width()); // wtf is this lol					
			// 	if ($('.modal-image').css('width') > window.innerWidth) {
			// 		let centerW = Math.round((window.innerWidth - parseInt($('.modal-image').css('width')))/2);
			// 		$('.modal').css('left',centerW);
			// 	}
			// }
			// else if ($('.modal-image').width() >= window.innerWidth) {
			// 	$('.modal').css('left', '0px');
			// 	$('.modal-image').css('width', $('.modal-image').width() + 'px');
			// 	$('.modal-image').css('height',$('.modal-image').height());
			// }
			scaleImage();
		});
	} else {
		//  TODO: rewrite the video part
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
	document.getElementsByClassName('modal')[0].addEventListener('mousedown', mouseDown, false);
}

const scaleImage = () => {
	// resets the image scale to fit the page
	let img = document.getElementById('centeredImage')
	var hRatio = window.innerWidth / img.naturalWidth;
	var vRatio = window.innerHeight / img.naturalHeight;
	var ratio  = Math.min(hRatio, vRatio);
	if (ratio < 1.0) {
		let newWidth = parseInt(img.naturalWidth * ratio);
		let newHeight = parseInt(img.naturalHeight * ratio);
		img.width = newWidth;
		img.height = newHeight;
		// img.style.width = `${img.width}px`;
		// img.style.height = `${img.height}px`;
		// console.log(img)
		let shiftX = (window.innerWidth - newWidth) / 2;
		let shiftY = (window.innerHeight - newHeight) / 2;
		img.style.left = `${shiftX}px`;
		img.style.top = `${shiftY}px`;
	} else {
		let shiftX = (window.innerWidth - img.naturalWidth) / 2;
		let shiftY = (window.innerHeight - img.naturalHeight) / 2;
		if (shiftX < 0) shiftX = 0;
		if (shiftY < 0) shiftY = 0;
		img.style.left = `${shiftX}px`;
		img.style.top = `${shiftY}px`;
	}
};

// $(document).ready(function(){
document.addEventListener('DOMContentLoaded', e => {
	[...document.getElementsByClassName('post-image')].map(element => {
		console.log(element)
		if (!element.classList.contains('modal-image')) {
			if (!element.tagName === 'IMG') files.push(element.getAttribute('data-image'));
		}
	});

	if (localStorage.volume === null || localStorage.volume === '' || typeof localStorage.volume === 'undefined') {
		localStorage.volume = 0.5;
	}

	// $('.modal').draggable();

	[...document.getElementsByClassName('modal-c')].map(element => {
		element.addEventListener('click', processModalClick)
	})

	$(document).on("click", function(event) {
		var target = $(event.target);
		if(target.hasClass('post-image')) {
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
				modalMedia.css('opacity', '');
				modalMedia.removeClass('post-image post-video post-media');
				$('#modalC').trigger('click');				
				if (!target.is('video')) {
					// look into this shitcode it might need rewriting
					var aspect = aspectRatio($('.modal-image'));
					let coef = 0.5;
					// done to avoid image getting fucked up while scrolling
					if ($('.modal-image').hasClass('fucked')) coef = coef * 0.15;
					var w = $('.modal-image').width() * aspect * coef;
					var h = $('.modal-image').height() * aspect * coef;
					centerModal();
					target.addClass('fucked');					
					$('.modal-image').on('wheel', function(e){
						var win = $(window);
						formX = intify('left');
						formY = intify('top');
						lastCursorX = e.pageX - win.scrollLeft();
						lastCursorY = e.pageY - win.scrollTop();
						cursorInBoxPosX = lastCursorX-formX;
						cursorInBoxPosY = lastCursorY-formY;
						var nwu = ($(this).width() + w ).toString();
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
				} else if (target.is('audio') || target.is('video')) {
					return false;
				}
				// } else {
				// 	centerModal();
				// 	var vid = $('.modal-image');
				// 	vid.attr('autoplay', '');
				// 	$(vid).on('loadeddata', function() {
				// 		var vw = vid[0].videoWidth;
				// 		var vh = vid[0].videoHeight;
				// 		if (vw <= $(window).width() &&  vh <= $(window).height()) {
				// 			vid.css('height', vh);
				// 			vid.css('width', vw);
				// 			centerModal();
				// 		} else {
				// 			vid.css('height', $(window).height());
				// 			vid.css('width', $(window).width());
				// 			centerModal();							 
				// 		}
				// 	});
				// 	var vol = parseFloat(localStorage.volume);
				// 	if (isNaN(vol)) {vol = 0.5};
				// 	if (vol > 1.0) {vol = 1.0};
				// 	if (vol < 0) {vol = 0.0};
				// 	vid.prop('volume', parseFloat(vol));
				// 	localStorage.volume = vol;
				// 	vid.on('DOMMouseScroll mousewheel wheel', function(e){
				// 		e.preventDefault();
				// 		vol = parseFloat(localStorage.volume);
				// 		if (vol > 1.0) {vol = 1.0};
				// 		if (vol < 0) {vol = 0.0};
				// 		vid.prop('volume', parseFloat(vol));
				// 		if(e.originalEvent.detail > 0 || e.originalEvent.wheelDelta < 0) {
				// 			var volume = (vol - 0.1);
				// 			localStorage.volume = volume;
				// 		} else {
				// 			var volume = (vol + 0.1);
				// 			localStorage.volume = volume;

				// 		}
				// 	});

				// }
			}
		} else {
			// horrible mess of if's
			if ($(target).parents().hasClass('modal')){
				if (!$(target).parents().hasClass('draggable')) {
					if ($(target).is(":visible") && $(target).is(":hover")) {
						$('.modal').empty();
						$('.modal-image').css('width', '0px').attr('top', 0).attr('left', 0);
						$('.modal-controls').hide();
					}
				}
			}
		}
	});

	function intify(shit) {
		return parseInt($('.modal').css(shit))
	}

	// broken if image exceeds window
	// replace form W and H with image ones?
});

function aspectRatio(element) {
    return $(element).width() / $(element).height();
}

// $.fn.draggable = function(){
//     var $this = this,
// 	ns = 'draggable_'+(Math.random()+'').replace('.',''),
// 	mm = 'mousemove.'+ns,
// 	mu = 'mouseup.'+ns,
// 	$w = $(window),
// 	isFixed = ($this.css('position') === 'fixed'),
// 	adjX = 0, adjY = 0;		
// 	$this.mousedown(function(ev){
// 		if (!$(ev.target).is('textarea') && !$(ev.target).is('input') && !$(ev.target).is('button')) {
// 			var pos = $this.offset();
// 			if (isFixed) {
// 				adjX = $w.scrollLeft(); adjY = $w.scrollTop();
// 			}
// 			var ox = (ev.pageX - pos.left), oy = (ev.pageY - pos.top);
// 			$this.data(ns,{ x : ox, y: oy });
// 			$w.on(mm, function(ev){
// 				$this.addClass('draggable');
// 				ev.preventDefault();
// 				ev.stopPropagation();
// 				if (isFixed) {
// 					adjX = $w.scrollLeft(); adjY = $w.scrollTop();
// 				}
// 				var offset = $this.data(ns);
// 				$this.css({left: ev.pageX - adjX - offset.x, top: ev.pageY - adjY - offset.y, cursor: 'move'});
// 			});
// 			$w.on(mu, function(){
// 				$w.off(mm + ' ' + mu).removeData(ns);
// 				setTimeout(function() {
// 					$this.removeClass('draggable');
// 					$this.css('cursor', 'pointer');
// 				}, 250);
// 			});
// 		};

// 		return this;
// 	})
// };
