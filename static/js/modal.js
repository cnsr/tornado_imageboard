let files = [];
//  this relies on the fact that there's only a single draggable element around 
let initX, initY, firstX, firstY;

const directionLeft = 'left', directionRight = 'right';

const processModalClick = (e) => {
	e.preventDefault();
	console.log('clicked on a button:', e.target)
	let fnext;
	if (e.target.id !== 'modalC') {
		let direction = e.target.id === 'modalL' ? directionLeft : directionRight;
		let allModalImages = document.getElementsByClassName('modal-image');
		if (allModalImages.length) {
			let current_index = files.indexOf(allModalImages[0].getAttribute('src'));
			let next_index = 0;
			switch (direction) {
				case directionLeft:
					next_index = current_index - 1;
					break;
				case directionRight:
					next_index = current_index + 1;
					break;
				default: break;
			}
			if (next_index < 0) next_index = files.length - 1;
			if (next_index > files.length - 1) next_index  = 0;
			fnext = files[next_index];
			let next_image = document.querySelectorAll(`*[data-image="${fnext}"]`)[0];
			if (next_image.length !== 1) {
				next_image = document.querySelectorAll(`video[src="${fnext}"]`)[0];
			}
			let post = next_image.closest('.oppost, .thread-outer, .post, .preview-post');
			[...document.getElementsByClassName('focused')].map(el => el.classList.remove('focused'));
			scrollToSmoothly(post.offset().top, 100)
			post.classList.add('focused');
			document.getElementById(next_image.id).click();
		}
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
	// document.getElementsByClassName('modal')[0].addEventListener('mousedown', mouseDown, false);
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
document.addEventListener('DOMContentLoaded', (e) => {
	[...document.getElementsByClassName('post-image')].map(element => {
		if (!element.classList.contains('modal-image')) {
			if (!element.tagName === 'IMG') files.push(element.getAttribute('data-image'));
		}
	});

	if (localStorage.volume === null || localStorage.volume === '' || typeof localStorage.volume === 'undefined') {
		localStorage.volume = 0.5;
	}

	[...document.getElementsByClassName('modal-c')].map(element => {
		element.addEventListener('click', processModalClick)
	});

	// TODO: refine selectors
	[
		...document.querySelectorAll('.post-image'),
		...document.querySelectorAll('.thread-media'),
		...document.querySelectorAll('.oppost-media'),
		...document.querySelectorAll('.post-video'),
	].map(el => {
		el.addEventListener('click', (e) => {
			let target = e.target;
			console.log('target', target);
			if (target.classList.contains('post-image')) {
				$('.modal-controls').css('display', 'block');
				if (target.closest('.modal') !== null) {
					let modal = target.closest('.modal');
					modal.innerHTML = null;
					// TODO: finish rewriting
					target.clone().appendTo('.modal');
					if (!target.is('video')) {
						$('.modal').find('img').attr('src', target.attr('data-image'));
					}
					// centering is broken, apparently, for images only, lol
					let modalMedia = $('.modal').find('.post-media');
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
						$('.modal-image').on('wheel', function (e) {
							var win = $(window);
							formX = intify('left');
							formY = intify('top');
							lastCursorX = e.pageX - win.scrollLeft();
							lastCursorY = e.pageY - win.scrollTop();
							cursorInBoxPosX = lastCursorX - formX;
							cursorInBoxPosY = lastCursorY - formY;
							var nwu = ($(this).width() + w).toString();
							var nhu = ($(this).height() + h).toString();
							var nwd = ($(this).width() - w).toString();
							var nhd = ($(this).height() - h).toString();
							if (e.originalEvent.deltaY > 0) {
								$(this).css("width", nwd);
								$(this).css("height", nhd);
								moveForm(lastCursorX - cursorInBoxPosX, lastCursorY - cursorInBoxPosY, true);
							} else {
								$(this).css("width", nwu);
								$(this).css("height", nhu);
								moveForm(lastCursorX - cursorInBoxPosX, lastCursorY - cursorInBoxPosY, false);
							}
							return false;
						});
					} else if (target.is('audio') || target.is('video')) {
						return false;
					}
				} else {
					console.log('there is no closest modal, need to spawn in');
					let container = document.getElementsByClassName('modal')[0];
					container.innerHTML = null;
					container.append(target.cloneNode(true));
					if (target.tagName == 'img') {
						let image = container.getElementsByTagName('img')[0];
						image.setAttribute(
							'src', target.getAttribute('data-image')
						);
						//	 TODO: make child draggable
					}
				}
			} else {
				console.log('there is no closest modal, need ti spawn in');
				let closestModalParent = target.closest('.modal');
				if (closestModalParent !== null) {
					let closestDraggableParent = target.closest('.modal');
					if (closestDraggableParent === null) {
						if (target.matches(":visible") && target.matches(":hover")) {
							[...document.getElementsByClassName('modal')].map(el => {
								el.innerHTML = null;
							});
							[...document.getElementsByClassName('modal-image')].map(el => {
								el.style.width = '0px';
								el.style.top = '0';
								el.style.left = '0';
							})
						}
					}
				}
			}
		});
	});
});

const intify = (property) => parseInt(document.getElementsByClassName('modal')[0].style[property]);

const aspectRatio = (element) => element.width / element.height;
